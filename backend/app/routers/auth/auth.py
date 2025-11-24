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

    # Brute force protection
    try:
        blocked = await is_blocked(ip=ip, identifier=identifier, redis=redis)
        if blocked:
            logger.warning(f"Blocked login attempt for {identifier} from {ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )
    except Exception as e:
        logger.warning(f"Redis unavailable for brute force check: {e}")

    # Find user
    db_user = UserCRUD.get_user_by_email(db, user_data.email)
    
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

        logger.warning(f"Failed login attempt for {user_data.email} from {ip}")
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
    
    logger.info(f"Successful login for user: {db_user.id} - {db_user.email}")
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