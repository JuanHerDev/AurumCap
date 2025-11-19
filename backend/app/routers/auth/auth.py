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

# ───────────────────────────────────────────
# utils locales (login/refresh local)
# ───────────────────────────────────────────
from app.utils.users import user as utils

# Middlewares
from app.deps.auth import get_current_user

# DB
from app.db.database import get_db
from app.models import user as user_models
from app.models.refresh_token import RefreshToken
from app.models.user import UserRole
from app.schemas import user as user_schema

# Redis
from app.core.redis_client import get_redis

# Settings
from app.core.config import settings

# Brute-force protection
from app.utils.alerts.bruteforce import is_blocked, record_failed_attempt, reset_attempts

# ───────────────────────────────────────────
# 🔥 NUEVO: AUTH MODERNO USANDO core/auth.py
# ───────────────────────────────────────────
from app.core.auth import (
    build_google_oauth_url,
    exchange_google_code_for_token,
    verify_google_id_token,
    create_access_token,
    create_user_session,
    destroy_user_session
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


REFRESH_COOKIE_PATH = "/auth"
IS_PROD = os.getenv("ENV") == "production"

# ============================================================
# LOCAL REGISTER
# ============================================================

@router.post("/register", response_model=user_schema.Token)
def register(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(user_models.User)
        .filter(user_models.User.email == user.email)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_pw = utils.hash_password(user.password)
    new_user = user_models.User(
        email=user.email,
        hashed_password=hashed_pw,
        auth_provider="local",
        is_active=True,
        role=UserRole.investor,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = utils.create_access_token(subject=new_user.id)

    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================
# LOCAL LOGIN + BRUTE FORCE PROTECTION
# ============================================================

@router.post("/login", response_model=user_schema.Token)
async def login(
    user: user_schema.UserLogin,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    ip = request.client.host if request.client else "unknown"
    identifier = user.email.lower()

    # Check brute-force
    try:
        blocked = await is_blocked(ip=ip, identifier=identifier, redis=redis)
    except Exception as e:
        logging.warning(f"Redis unavailable: {e}")
        blocked = False

    if blocked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    db_user = (
        db.query(user_models.User)
        .filter(user_models.User.email == user.email)
        .first()
    )

    valid_login = (
        db_user
        and db_user.hashed_password
        and utils.verify_password(user.password, db_user.hashed_password)
    )

    if not valid_login:
        try:
            await record_failed_attempt(ip=ip, identifier=identifier, redis=redis, request=request)
        except Exception:
            pass

        raise HTTPException(status_code=401, detail="Invalid email or password")

    await reset_attempts(ip=ip, identifier=identifier, redis=redis)

    # Access + Refresh
    access_token = utils.create_access_token(subject=db_user.id)
    raw_refresh, expires_at = utils.create_refresh_token(subject=db_user.id)
    hashed = utils.hash_token(raw_refresh)

    rt = RefreshToken(
        user_id=db_user.id,
        token_hash=hashed,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip=ip,
    )
    db.add(rt)
    db.commit()

    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_refresh,
        httponly=True,
        secure=settings.IS_PROD,
        samesite="none" if settings.IS_PROD else "lax",
        path=settings.REFRESH_COOKIE_PATH,
        expires=int((expires_at - datetime.now(timezone.utc)).total_seconds()),
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================
# 🔥🔥 GOOGLE OAUTH USANDO core/auth.py 🔥🔥
# ============================================================

@router.get("/login/google")
async def login_google():
    """Devuelve la URL para iniciar sesión con Google."""
    return {"auth_url": build_google_oauth_url()}


@router.get("/oauth/google/callback", response_model=user_schema.Token)
async def google_callback(
    code: str,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Paso final del login con Google.
    """

    # 1) Intercambiar code por tokens
    tokens = await exchange_google_code_for_token(code)

    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(400, "Google did not return id_token")

    # 2) Verificar ID Token
    google_user = await verify_google_id_token(id_token)
    email = google_user.get("email")

    if not email:
        raise HTTPException(400, "Google did not return email")

    # 3) Buscar / crear usuario
    user = (
        db.query(user_models.User)
        .filter_by(email=email)
        .first()
    )

    if not user:
        user = user_models.User(
            email=email,
            full_name=google_user.get("name"),
            picture_url=google_user.get("picture"),
            auth_provider="google",
            is_active=True,
            role=UserRole.investor,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4) Crear sesión en Redis
    await create_user_session(email, redis)

    # 5) Crear Access Token
    access_token = create_access_token({"sub": email})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============================================================
# REFRESH TOKEN (ROTATION)
# ============================================================

@router.post("/refresh", response_model=user_schema.Token)
def refresh_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None, alias=settings.REFRESH_COOKIE_NAME),
):
    if not refresh_token:
        raise HTTPException(401, "Missing refresh token")

    hashed = utils.hash_token(refresh_token)
    db_rt = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed).first()

    if not db_rt or db_rt.revoked:
        raise HTTPException(401, "Invalid refresh token")

    now = datetime.now(timezone.utc)

    expires = db_rt.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires < now:
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.get(user_models.User, db_rt.user_id)
    if not user:
        raise HTTPException(401, "User not found")

    db_rt.revoked = True
    db.add(db_rt)

    new_access = utils.create_access_token(subject=user.id)
    raw_new_refresh, expires_at = utils.create_refresh_token(subject=user.id)
    new_hash = utils.hash_token(raw_new_refresh)

    new_db_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(new_db_rt)
    db.commit()

    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_new_refresh,
        httponly=True,
        secure=settings.IS_PROD,
        samesite="none" if settings.IS_PROD else "lax",
        path=settings.REFRESH_COOKIE_PATH,
        expires=int((expires_at - datetime.now(timezone.utc)).total_seconds()),
    )

    return {"access_token": new_access, "token_type": "bearer"}


# ============================================================
# LOGOUT
# ============================================================

@router.post("/logout")
async def logout(
    response: Response,
    current_user: user_models.User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    refresh_token: Optional[str] = Cookie(None, alias=settings.REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db)
):
    # Destruir sesión en Redis
    await destroy_user_session(current_user.email, redis)

    # Revocar Refresh Token en DB
    if refresh_token:
        hashed = utils.hash_token(refresh_token)
        db_rt = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed).first()
        if db_rt:
            db_rt.revoked = True
            db.add(db_rt)
            db.commit()

    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )

    return {"detail": "Logged out successfully"}


# ============================================================
# /ME
# ============================================================

@router.get("/me")
def get_me(current_user: user_models.User = Depends(get_current_user)):
    return current_user
