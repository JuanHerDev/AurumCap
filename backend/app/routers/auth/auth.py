from fastapi import (
    APIRouter, Depends, HTTPException, status, Query,
    Response, Cookie, Request
)
from sqlalchemy.orm import Session
from redis.asyncio import Redis
from typing import Optional
from datetime import datetime, timezone
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
IS_PROD = settings.IS_PROD  # <-- MEJOR: Usar settings en lugar de os.getenv

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
    request: Request,  # <-- PRIMERO los parámetros sin default
    user_data: user_schema.UserCreate,  # <-- LUEGO el body
    db: Session = Depends(get_db)  # <-- FINAL los Depends()
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
        tokens = AuthService._create_user_session(db, new_user, request)  # <-- Ahora request está disponible

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
    return {"auth_url": build_google_oauth_url()}

@router.get("/oauth/google/callback", response_model=user_schema.Token)
async def google_callback(
    code: str,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Google OAuth callback handler"""
    try:
        # 1. Exchange code for tokens
        tokens = await exchange_google_code_for_token(code)
        id_token = tokens.get("id_token")
        
        if not id_token:
            raise HTTPException(400, "Google did not return ID token")

        # 2. Verify ID token
        google_user = await verify_google_id_token(id_token)
        email = google_user.get("email")
        
        if not email:
            raise HTTPException(400, "Google did not return email")

        # 3. Find or create user
        user = UserCRUD.get_user_by_email(db, email)
        if not user:
            user = UserCRUD.create_user(
                db=db,
                email=email,
                full_name=google_user.get("name"),
                auth_provider=AuthProviderEnum.google,
                picture_url=google_user.get("picture"),
                role=UserRole.investor
            )
        else:
            # Update user info if needed
            if google_user.get("picture") and not user.picture_url:
                user.picture_url = google_user.get("picture")
            if google_user.get("name") and not user.full_name:
                user.full_name = google_user.get("name")
            db.commit()

        # 4. Create tokens and set cookies
        tokens = AuthService._create_user_session(db, user, request, response)
        
        logger.info(f"Google OAuth successful for user: {user.id} - {user.email}")
        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(500, "OAuth authentication failed")

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