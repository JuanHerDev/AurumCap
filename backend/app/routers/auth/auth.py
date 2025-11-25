from fastapi import (
    APIRouter, Depends, HTTPException, status, Query,
    Response, Cookie, Request
)
import httpx
from sqlalchemy.orm import Session
from redis.asyncio import Redis
from typing import Optional
from datetime import datetime, timezone
from fastapi.responses import HTMLResponse
import logging
import os

# Local imports
from app.utils.users import user as utils
from app.deps.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.models import user as user_models
from app.models.refresh_token import RefreshToken
from app.models.user import UserRole, AuthProviderEnum
from app.schemas import user as user_schema
from app.schemas.user import PasswordChange, UserResponse
from app.crud.user import UserCRUD
from app.core.redis_client import get_redis
from app.core.config import settings

# Brute Force protection
from app.utils.alerts.bruteforce import is_blocked, record_failed_attempt, reset_attempts

# Google OAuth
from app.core.auth import (
    build_google_oauth_url,
    exchange_google_code_for_token,
    verify_google_id_token
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_PATH = "/auth/refresh"
IS_PROD = settings.IS_PROD

class AuthService:
    """Service class for authentication business logic"""
    
    @staticmethod
    def _set_refresh_cookie(
        response: Response,
        refresh_token: str,
        expires_at: datetime
    ) -> None:
        """Safely set refresh token cookie"""
        try:
            max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=refresh_token,
                httponly=True,
                secure=IS_PROD,
                samesite="lax" if not IS_PROD else "none",
                path=REFRESH_COOKIE_PATH,
                max_age=max_age,
            )
        except Exception as e:
            logger.error(f"Error setting refresh cookie: {e}")
            raise

    @staticmethod
    def _create_user_session(
        db: Session,
        user: user_models.User,
        request: Request,
        response: Response = None
    ) -> dict:
        """Create access and refresh tokens for user"""
        # Create access token
        access_token = utils.create_access_token(subject=user.id)
        
        # Create refresh token
        raw_refresh, expires_at = utils.create_refresh_token(subject=user.id)
        hashed_refresh = utils.hash_token(raw_refresh)

        # Store refresh token in database
        ip = request.client.host if request.client else "unknown"
        rt = RefreshToken(
            user_id=user.id,
            token_hash=hashed_refresh,
            expires_at=expires_at,
            user_agent=request.headers.get("user-agent"),
            ip=ip,
        )
        db.add(rt)
        db.commit()

        # Set refresh cookie if response provided
        if response:
            AuthService._set_refresh_cookie(response, raw_refresh, expires_at)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": raw_refresh if not response else None
        }

@router.post("/register", response_model=user_schema.Token)
def register(
    request: Request,
    user_data: user_schema.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new local user
    """
    try:
        # Validate password strength
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

        # Check if user already exists
        existing_user = UserCRUD.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password
        hashed_pw = utils.hash_password(user_data.password)

        # Create user
        new_user = UserCRUD.create_user(
            db=db,
            email=user_data.email,
            password_hash=hashed_pw,
            full_name=user_data.full_name,
            auth_provider=AuthProviderEnum.local,
            role=UserRole.investor
        )

        # Create session (without response for register)
        tokens = AuthService._create_user_session(db, new_user, request)

        return tokens

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error for {user_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    

@router.post("/login", response_model=user_schema.Token)
async def login(
    user_data: user_schema.UserLogin,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Local email/password login
    """
    ip = request.client.host if request.client else "unknown"
    identifier = user_data.email.lower()

    logger.info(f"🔐 Intento de login para: {identifier} desde {ip}")

    # Brute force protection
    try:
        blocked = await is_blocked(ip=ip, identifier=identifier, redis=redis)
        if blocked:
            logger.warning(f"🚫 Login bloqueado por brute force: {identifier} desde {ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )
    except Exception as e:
        logger.warning(f"Redis unavailable for brute force check: {e}")

    # Find user
    db_user = UserCRUD.get_user_by_email(db, user_data.email)
    logger.info(f"👤 Usuario encontrado: {db_user.id if db_user else 'No encontrado'}")
    
    # Validate credentials
    valid_login = (
        db_user 
        and db_user.is_active
        and db_user.hashed_password
        and db_user.auth_provider == AuthProviderEnum.local
        and utils.verify_password(user_data.password, db_user.hashed_password)
    )

    if not valid_login:
        # Record failed attempt
        try:
            await record_failed_attempt(ip=ip, identifier=identifier, redis=redis, request=request)
        except Exception as e:
            logger.warning(f"Could not record failed attempt: {e}")

        logger.warning(f"❌ Login fallido para {user_data.email} desde {ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password"
        )

    # Reset attempt counter on successful login
    try:
        await reset_attempts(ip=ip, identifier=identifier, redis=redis)
    except Exception as e:
        logger.warning(f"Could not reset attempt counter: {e}")

    # Create user session
    tokens = AuthService._create_user_session(db, db_user, request, response)
    
    logger.info(f"✅ Login exitoso para usuario: {db_user.id} - {db_user.email}")
    return tokens

@router.get("/login/google")
async def login_google():
    """Initiate Google OAuth flow"""
    try:
        logger.info("🔄 Iniciando flujo de Google OAuth")
        
        # Verificar configuración
        if not hasattr(settings, 'GOOGLE_CLIENT_ID') or not settings.GOOGLE_CLIENT_ID:
            logger.error("❌ GOOGLE_CLIENT_ID no configurado en settings")
            raise HTTPException(
                status_code=500,
                detail="Google OAuth no está configurado. Verifica las variables de entorno."
            )
        
        logger.info(f"🔧 Client ID: {settings.GOOGLE_CLIENT_ID[:25]}...")
        logger.info(f"🔧 Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
        
        # Generar URL
        auth_url = build_google_oauth_url()
        
        logger.info(f"✅ URL de Google OAuth generada exitosamente")
        
        return {
            "auth_url": auth_url,
            "message": "Redirige al usuario a esta URL para autenticar con Google"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en login_google: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando autenticación con Google: {str(e)}"
        )

@router.get("/login/google/debug")
async def login_google_debug():
    """Debug específico para el endpoint de Google"""
    try:
        logger.info("🔧 DEBUG: Ejecutando login_google_debug")
        
        # Test 1: Verificar settings
        google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', 'NOT_SET')
        google_client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', 'NOT_SET')
        
        logger.info(f"🔧 DEBUG - GOOGLE_CLIENT_ID: {google_client_id[:20] if google_client_id != 'NOT_SET' else 'NOT_SET'}...")
        logger.info(f"🔧 DEBUG - GOOGLE_CLIENT_SECRET configurado: {bool(google_client_secret and google_client_secret != 'NOT_SET')}")
        
        # Test 2: Verificar función build_google_oauth_url
        try:
            from app.core.auth import build_google_oauth_url
            auth_url = build_google_oauth_url()
            logger.info(f"🔧 DEBUG - URL generada: {auth_url[:100]}...")
            
            return {
                "status": "success",
                "client_id_configured": bool(google_client_id and google_client_id != 'NOT_SET'),
                "client_secret_configured": bool(google_client_secret and google_client_secret != 'NOT_SET'),
                "auth_url_generated": True,
                "auth_url_preview": auth_url[:100] + "..." if len(auth_url) > 100 else auth_url
            }
            
        except Exception as e:
            logger.error(f"🔧 DEBUG - Error en build_google_oauth_url: {str(e)}")
            return {
                "status": "error",
                "error": f"build_google_oauth_url failed: {str(e)}",
                "client_id_configured": bool(google_client_id and google_client_id != 'NOT_SET'),
                "client_secret_configured": bool(google_client_secret and google_client_secret != 'NOT_SET')
            }
            
    except Exception as e:
        logger.error(f"🔧 DEBUG - Error general: {str(e)}")
        return {"status": "error", "error": str(e)}

@router.get("/oauth/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(..., description="Google authorization code"),
    error: str = Query(None),
    db: Session = Depends(get_db),
):
    """Google OAuth callback handler - USA sessionStorage"""
    try:
        logger.info(f"🔄 Google callback recibido - código: {code[:30]}...")
        
        if error:
            logger.error(f"❌ Error de Google OAuth: {error}")
            raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
        
        # ✅ MOCK FUNCIONAL
        import hashlib
        code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
        mock_email = f"google.user.{code_hash}@example.com"
        mock_name = f"Google User {code_hash}"
        
        logger.info(f"🔧 MOCK - Usando usuario: {mock_email}")

        user = UserCRUD.get_user_by_email(db, mock_email)
        if not user:
            user = UserCRUD.create_user(
                db=db,
                email=mock_email,
                full_name=mock_name,
                auth_provider=AuthProviderEnum.google,
                picture_url=f"https://avatars.dicebear.com/api/human/{code_hash}.svg",
                role=UserRole.investor
            )
            logger.info(f"👤 Nuevo usuario MOCK creado: {user.id}")

        access_token = utils.create_access_token(subject=user.id)
        
        logger.info(f"✅ Google OAuth MOCK successful for user: {user.id} - {user.email}")
        
        # ✅ CORREGIDO: Usar slicing de Python en lugar de substring de JS
        token_preview = access_token[:50] + "..." if access_token else ""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redirigiendo...</title>
        </head>
        <body>
            <script>
                console.log('🔑 Google OAuth exitoso - Guardando token en SESSIONSTORAGE...');
                console.log('👤 Usuario: {mock_email}');
                
                // ✅ GUARDAR EN SESSIONSTORAGE
                sessionStorage.setItem('access_token', '{access_token}');
                sessionStorage.setItem('user_email', '{mock_email}');
                sessionStorage.setItem('auth_provider', 'google');
                
                console.log('✅ Token guardado en sessionStorage, redirigiendo...');
                console.log('🔍 Token: {token_preview}');
                
                // Verificar que se guardó correctamente
                const savedToken = sessionStorage.getItem('access_token');
                if (savedToken === '{access_token}') {{
                    console.log('✅ Verificación: Token guardado correctamente');
                }} else {{
                    console.error('❌ Verificación: Token no se guardó correctamente');
                }}
                
                // Redirigir al dashboard
                setTimeout(function() {{
                    window.location.href = 'http://localhost:3000/dashboard';
                }}, 100);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"❌ Google OAuth MOCK error: {str(e)}", exc_info=True)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script>
                console.error('❌ Error en autenticación Google: {str(e)}');
                window.location.href = 'http://localhost:3000/login?error=google_auth_failed&message={str(e)}';
            </script>
        </head>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=500)

@router.post("/refresh", response_model=user_schema.Token)
async def refresh_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None, alias=settings.REFRESH_COOKIE_NAME),
):
    """Refresh access token using refresh token"""
    if not refresh_token:
        raise HTTPException(401, "Missing refresh token")

    try:
        hashed = utils.hash_token(refresh_token)
        db_rt = db.query(RefreshToken).filter(
            RefreshToken.token_hash == hashed,
            RefreshToken.revoked == False
        ).first()

        if not db_rt:
            raise HTTPException(401, "Invalid refresh token")

        # Check expiration
        now = datetime.now(timezone.utc)
        if db_rt.expires_at.replace(tzinfo=timezone.utc) < now:
            # Mark as revoked
            db_rt.revoked = True
            db.commit()
            raise HTTPException(401, "Refresh token expired")

        # Get user
        user = UserCRUD.get_user_by_id(db, db_rt.user_id)
        if not user or not user.is_active:
            raise HTTPException(401, "User not found or inactive")

        # Revoke old token
        db_rt.revoked = True
        db.add(db_rt)

        # Create new tokens
        tokens = AuthService._create_user_session(db, user, request, response)

        logger.info(f"Token refreshed for user: {user.id}")
        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(500, "Token refresh failed")

@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: user_models.User = Depends(get_current_user_optional),
    redis: Redis = Depends(get_redis),
    refresh_token: Optional[str] = Cookie(None, alias=settings.REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db)
):
    """Logout user and revoke tokens"""
    try:
        # Revoke refresh token
        if refresh_token:
            hashed = utils.hash_token(refresh_token)
            db_rt = db.query(RefreshToken).filter(
                RefreshToken.token_hash == hashed
            ).first()
            if db_rt:
                db_rt.revoked = True
                db.add(db_rt)
                db.commit()

        # Clear refresh cookie
        response.delete_cookie(
            key=settings.REFRESH_COOKIE_NAME,
            path=REFRESH_COOKIE_PATH,
        )

        logger.info(f"User logged out: {current_user.id if current_user else 'Unknown'}")
        return {"detail": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(500, "Logout failed")

@router.get("/me", response_model=user_schema.UserResponse)
async def get_me(current_user: user_models.User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.put("/me/password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password
    """
    try:
        logger.info(f"===== INICIANDO CAMBIO DE CONTRASEÑA =====")
        logger.info(f"Usuario: {current_user.id} - {current_user.email}")
        
        # ===== DEBUG 1: INFORMACIÓN INICIAL =====
        logger.info(f"[DEBUG-1] Contraseña actual ingresada: '{password_data.current_password}'")
        logger.info(f"[DEBUG-1] Longitud contraseña actual: {len(password_data.current_password)}")
        logger.info(f"[DEBUG-1] Hash almacenado en BD: {current_user.hashed_password}")
        logger.info(f"[DEBUG-1] Longitud hash: {len(current_user.hashed_password) if current_user.hashed_password else 0}")

        # ===== VERIFICACIÓN CONTRASEÑA ACTUAL =====
        logger.info(f"Verificando contraseña actual...")
        is_current_valid = utils.verify_password(password_data.current_password, current_user.hashed_password)
        logger.info(f"[DEBUG-2] Resultado verificación actual: {is_current_valid}")
        
        if not is_current_valid:
            logger.warning(f"[ERROR] Contraseña actual incorrecta para usuario {current_user.email}")
            # Debug adicional para entender por qué falla
            test_hash = utils.hash_password(password_data.current_password)
            logger.info(f"[DEBUG-2a] Hash de prueba con misma contraseña: {test_hash}")
            logger.info(f"[DEBUG-2b] ¿Verifica el hash de prueba?: {utils.verify_password(password_data.current_password, test_hash)}")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual es incorrecta"
            )
        
        logger.info("✅ Contraseña actual verificada correctamente")

        # ===== VERIFICACIÓN CONTRASEÑA NUEVA =====
        logger.info(f"[DEBUG-3] Nueva contraseña: '{password_data.new_password}'")
        logger.info(f"[DEBUG-3] Longitud nueva contraseña: {len(password_data.new_password)}")
        
        is_same_password = utils.verify_password(password_data.new_password, current_user.hashed_password)
        logger.info(f"[DEBUG-4] ¿Nueva contraseña igual a actual?: {is_same_password}")
        
        if is_same_password:
            logger.warning(f"Nueva contraseña igual a la actual para usuario {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva contraseña no puede ser igual a la actual"
            )

        # ===== VALIDACIÓN FUERZA CONTRASEÑA =====
        try:
            user_schema.UserCreate(password=password_data.new_password, email=current_user.email)
            logger.info("Nueva contraseña cumple con los requisitos de seguridad")
        except ValueError as e:
            logger.warning(f"Nueva contraseña no cumple requisitos: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # ===== HASH NUEVA CONTRASEÑA =====
        logger.info("Generando nuevo hash...")
        new_hashed_password = utils.hash_password(password_data.new_password)
        logger.info(f"[DEBUG-5] Nuevo hash generado: {new_hashed_password}")
        logger.info(f"[DEBUG-5] Longitud nuevo hash: {len(new_hashed_password)}")
        
        # Test del nuevo hash inmediatamente
        is_new_hash_valid = utils.verify_password(password_data.new_password, new_hashed_password)
        logger.info(f"[DEBUG-6] ¿El nuevo hash verifica correctamente?: {is_new_hash_valid}")

        # ===== ACTUALIZACIÓN BASE DE DATOS =====
        logger.info(f"Actualizando base de datos...")
        logger.info(f"[DEBUG-7] Hash ANTES de actualizar: {current_user.hashed_password}")
        
        current_user.hashed_password = new_hashed_password
        db.commit()
        logger.info("Commit realizado")
        
        db.refresh(current_user)
        logger.info("Usuario refrescado en sesión")

        # ===== VERIFICACIÓN POST-ACTUALIZACIÓN =====
        logger.info("Verificando actualización en BD...")
        fresh_user = UserCRUD.get_user_by_email(db, current_user.email)
        if fresh_user:
            logger.info(f"[DEBUG-8] Hash en BD después del commit: {fresh_user.hashed_password}")
            logger.info(f"[DEBUG-8] Longitud hash en BD: {len(fresh_user.hashed_password) if fresh_user.hashed_password else 0}")
            logger.info(f"[DEBUG-9] ¿Coincide con el nuevo hash?: {fresh_user.hashed_password == new_hashed_password}")
            
            # Test de verificación con el usuario fresco de la BD
            fresh_verify = utils.verify_password(password_data.new_password, fresh_user.hashed_password)
            logger.info(f"[DEBUG-10] ¿La nueva contraseña verifica con BD?: {fresh_verify}")
            
            # Test de verificación con el usuario en sesión
            session_verify = utils.verify_password(password_data.new_password, current_user.hashed_password)
            logger.info(f"[DEBUG-11] ¿La nueva contraseña verifica con sesión?: {session_verify}")
        else:
            logger.error("No se pudo obtener usuario fresco de la BD")

        # ===== VERIFICACIÓN CONTRASEÑA ANTERIOR =====
        old_password_still_works = utils.verify_password(password_data.current_password, current_user.hashed_password)
        logger.info(f"[DEBUG-12] ¿La contraseña anterior aún funciona?: {old_password_still_works}")

        logger.info(f"===== CAMBIO DE CONTRASEÑA COMPLETADO =====")
        logger.info(f"Contraseña cambiada exitosamente para usuario {current_user.email}")

        return {
            "message": "Contraseña actualizada exitosamente",
            "detail": "Tu contraseña ha sido cambiada correctamente"
        }
        
    except HTTPException:
        logger.error("===== CAMBIO DE CONTRASEÑA FALLIDO - HTTPException =====")
        raise
    except Exception as e:
        logger.error(f"===== CAMBIO DE CONTRASEÑA FALLIDO - Error crítico =====")
        logger.error(f"Error: {e}")
        logger.error(f"ipo de error: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cambiar la contraseña"
        )

@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    user_update: user_schema.UserUpdate,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    try:
        updated_user = UserCRUD.update_user(
            db=db,
            user_id=current_user.id,
            update_data=user_update.model_dump(exclude_unset=True)
        )
        return updated_user
    except Exception as e:
        logger.error(f"Error updating user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la información del usuario"
        )

@router.post("/debug-password")
async def debug_password(
    debug_data: dict,
    db: Session = Depends(get_db)
):
    """
    Endpoint temporal para debuggear contraseñas
    """
    try:
        email = debug_data.get("email")
        password_to_test = debug_data.get("password")
        
        logger.info(f"🔧 ===== DEBUG PASSWORD =====")
        logger.info(f"🔧 Email: {email}")
        logger.info(f"🔧 Contraseña a testear: '{password_to_test}'")
        
        user = UserCRUD.get_user_by_email(db, email)
        if not user:
            logger.warning(f"🔧 Usuario no encontrado: {email}")
            return {"error": "Usuario no encontrado"}
        
        # Test de hash/verify
        test_hash = utils.hash_password(password_to_test)
        test_verify = utils.verify_password(password_to_test, test_hash)
        current_verify = utils.verify_password(password_to_test, user.hashed_password)
        
        logger.info(f"Hash almacenado en BD: {user.hashed_password}")
        logger.info(f"Nuevo hash de prueba: {test_hash}")
        logger.info(f"¿El nuevo hash verifica?: {test_verify}")
        logger.info(f"¿La contraseña actual verifica?: {current_verify}")
        logger.info(f"¿Son el mismo hash?: {user.hashed_password == test_hash}")
        
        return {
            "user_id": user.id,
            "email": user.email,
            "stored_hash": user.hashed_password,
            "new_test_hash": test_hash,
            "test_hash_works": test_verify,
            "current_password_works": current_verify,
            "same_hash": user.hashed_password == test_hash
        }
    except Exception as e:
        logger.error(f"💥 Error en debug: {e}")
        return {"error": str(e)}

@router.get("/test-google-config")
async def test_google_config():
    """Test endpoint para verificar configuración de Google"""
    return {
        "client_id": settings.GOOGLE_CLIENT_ID[:20] + "..." if settings.GOOGLE_CLIENT_ID else "MISSING",
        "client_secret": "***" + settings.GOOGLE_CLIENT_SECRET[-4:] if settings.GOOGLE_CLIENT_SECRET else "MISSING",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "auth_url": build_google_oauth_url()
    }

@router.get("/test-google-connection")
async def test_google_connection():
    """Test endpoint para verificar conexión con Google"""
    try:
        # Test simple de conexión a Google
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.googleapis.com/oauth2/v3/certs", timeout=10.0)
            
        return {
            "status": "success" if response.status_code == 200 else "failed",
            "google_api_status": response.status_code,
            "message": "Conexión a Google API exitosa" if response.status_code == 200 else "Error conectando a Google API"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error de conexión: {str(e)}"
        }
    
@router.get("/debug-google-token")
async def debug_google_token(
    code: str = Query(..., description="Google authorization code to test")
):
    """Debug endpoint para probar el intercambio de tokens"""
    try:
        logger.info(f"🧪 DEBUG: Probando intercambio de token con código: {code[:50]}...")
        
        # Verificar credenciales
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            return {
                "status": "error",
                "message": "Credenciales de Google no configuradas"
            }
        
        # Preparar datos para la solicitud
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        }
        
        logger.info(f"🧪 DEBUG: Enviando a Google...")
        logger.info(f"🧪 DEBUG - Client ID: {settings.GOOGLE_CLIENT_ID}")
        logger.info(f"🧪 DEBUG - Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
        logger.info(f"🧪 DEBUG - Code length: {len(code)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0
            )
            
            logger.info(f"🧪 DEBUG - Respuesta de Google: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                return {
                    "status": "success",
                    "message": "Token exchange successful",
                    "token_type": token_data.get("token_type"),
                    "access_token_length": len(token_data.get("access_token", "")),
                    "id_token_present": "id_token" in token_data,
                    "scope": token_data.get("scope", "")
                }
            else:
                error_text = response.text
                logger.error(f"🧪 DEBUG - Error de Google: {response.status_code} - {error_text}")
                return {
                    "status": "error",
                    "message": f"Google returned error: {response.status_code}",
                    "error_details": error_text,
                    "redirect_uri_used": settings.GOOGLE_REDIRECT_URI
                }
                
    except Exception as e:
        logger.error(f"🧪 DEBUG - Exception: {str(e)}")
        return {
            "status": "error",
            "message": f"Exception: {str(e)}"
        }

@router.get("/test-google-flow")
async def test_google_flow():
    """Genera una URL de prueba para el flujo de Google"""
    return {
        "auth_url": build_google_oauth_url(),
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "instructions": "Usa la auth_url en el navegador, autoriza y copia el código del parámetro 'code' de la URL de callback"
    }

@router.get("/test-routes")
async def test_routes():
    """Test endpoint para verificar que las rutas funcionan"""
    return {
        "message": "Auth router está funcionando",
        "available_routes": [
            "/auth/test-routes",
            "/auth/login/google", 
            "/auth/oauth/google/callback",
            "/auth/login",
            "/auth/register"
        ]
    }