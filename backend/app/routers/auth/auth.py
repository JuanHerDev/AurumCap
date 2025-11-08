from fastapi import (
    APIRouter, Depends, HTTPException, status, Query,
    Response, Cookie, Request
)
from sqlalchemy.orm import Session
from jose import JWTError
from datetime import datetime, timedelta, timezone
from redis.asyncio import Redis
from typing import Optional
import logging
import os
import asyncio

from app.utils.users import user as utils
from app.db.database import get_db
from app.models import user as user_models
from app.models.refresh_token import RefreshToken
from app.models.user import UserRole
from app.schemas import user as user_schema
from app.core.redis_client import get_redis
from app.core.config import settings
from app.utils.auth.oauth import verify_google_token
from app.utils.alerts.bruteforce import is_blocked, record_failed_attempt, reset_attempts

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "aurum_refresh_token"
REFRESH_COOKIE_PATH = "/auth"

# Detect if it is in a production environment (for secure cookies)
IS_PROD = os.getenv("ENV") == "production"


# Local Register

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
        role=UserRole.investor,  # Default role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = utils.create_access_token(subject=new_user.id)
    return {"access_token": access_token, "token_type": "bearer"}


# Local login with brute-force protection

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

    # Check if it is blocked (handle Redis error without breaking login)
    try:
        blocked = await is_blocked(ip=ip, identifier=identifier, redis=redis)
    except Exception as e:
        logging.warning(f"Redis unavailable during brute-force check: {e}")
        blocked = False

    if blocked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    # Search user
    db_user = (
        db.query(user_models.User)
        .filter(user_models.User.email == user.email)
        .first()
    )

    # Verify credentials
    valid_login = (
        db_user
        and db_user.hashed_password
        and utils.verify_password(user.password, db_user.hashed_password)
    )

    if not valid_login:
        try:
            await record_failed_attempt(ip=ip, identifier=identifier, redis=redis, request=request)
        except Exception as e:
            logging.warning(f"Redis unavailable during failed attempt record: {e}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Reset the failed attempts counter if the login is successful
    try:
        await reset_attempts(ip=ip, identifier=identifier, redis=redis)
    except Exception as e:
        logging.warning(f"Redis unavailable during reset_attempts: {e}")

    # Create tokens
    access_token = utils.create_access_token(subject=db_user.id)

    # Create refresh token and save hash in DB
    raw_refresh = utils.create_refresh_token(subject=db_user.id)
    hashed = utils.hash_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=utils.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        user_id=db_user.id,
        token_hash=hashed,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip=ip,
    )
    db.add(rt)
    db.commit()

    # Send httpOnly + Secure cookie (depending on the environment)
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_refresh,
        httponly=True,
        secure=settings.IS_PROD,  # True in production with HTTPS
        samesite="none" if settings.IS_PROD else "lax",
        path=settings.REFRESH_COOKIE_PATH,
        expires=int((expires_at - datetime.now(timezone.utc)).total_seconds()),
    )

    return {"access_token": access_token, "token_type": "bearer"}


# OAuth (Google)
@router.post("/oauth/{provider}", response_model=user_schema.Token)
def oauth_login(provider: str, token: str, db: Session = Depends(get_db)):
    if provider == "google":
        user_info = verify_google_token(token)
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Search or create user
    user = db.query(user_models.User).filter_by(email=user_info["email"]).first()
    if not user:
        user = user_models.User(
            email=user_info["email"],
            full_name=user_info.get("name"),
            picture_url=user_info.get("picture"),
            auth_provider=provider,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create token
    access_token = utils.create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


# Refresh Token (security rotation)
@router.post("/refresh", response_model=user_schema.Token)
def refresh_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_COOKIE_NAME),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    hashed = utils.hash_token(refresh_token)
    db_rt = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed).first()

    if not db_rt or db_rt.revoked:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if db_rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.get(user_models.User, db_rt.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Revoke older token
    db_rt.revoked = True
    db.add(db_rt)

    # Create new access token
    new_access = utils.create_access_token(subject=user.id)

    # Rotate refresh token
    raw_new_refresh = utils.create_refresh_token(subject=user.id)
    new_hash = utils.hash_token(raw_new_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=utils.REFRESH_TOKEN_EXPIRE_DAYS)

    new_db_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(new_db_rt)
    db.commit()

    # Rewrite cookie
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


# Logout (revoke token + delete cookie)
@router.post("/logout")
def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db),
):
    if refresh_token:
        hashed = utils.hash_token(refresh_token)
        db_rt = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed).first()
        if db_rt:
            db_rt.revoked = True
            db.add(db_rt)
            db.commit()

    # Delete user cookie
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )

    return {"detail": "Logged out successfully"}


# Get current user
@router.get("/me")
def get_me(current_user: user_models.User = Depends(utils.get_current_user)):
    """Returns the authenticated user's information based on the access token"""
    return current_user
