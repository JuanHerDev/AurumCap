from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Cookie, Request
from sqlalchemy.orm import Session
from jose import JWTError
from datetime import datetime, timedelta, timezone
from app.utils import user as utils
from app.db.database import get_db
from app.models import user as user_models
from app.models.refresh_token import RefreshToken
from app.models.user import UserRole
from app.schemas import user as user_schema
from redis.asyncio import Redis
from app.core.security import get_current_token
from app.core.redis_client import get_redis
from app.utils.oauth import verify_google_token
from app.utils.bruteforce import is_blocked, record_failed_attempt, reset_attempts
import asyncio

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

REFRESH_COOKIE_NAME = "aurum_refresh_token"
REFRESH_COOKIE_PATH = "/auth"


"""
Local Register
"""
@router.post("/register", response_model=user_schema.Token)
def register(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(user_models.User).filter(user_models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_pw = utils.hash_password(user.password)
    new_user = user_models.User(
            email=user.email,
            hashed_password=hashed_pw,
            auth_provider="local",
            is_active=True,
            role=UserRole.investor # Default role
        )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = utils.create_access_token(subject=new_user.id)
    return {"access_token": access_token, "token_type": "bearer"}

"""
Local Login
"""
@router.post("/login", response_model=user_schema.Token)
async def login(user: user_schema.UserLogin, response: Response, request: Request, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):

    ip = request.client.host if request.client else "unknown"
    identifier = user.email.lower()

    # Check if blocked
    if await is_blocked(ip=ip, identifier=identifier, redis=redis):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later."
        )
    
    # Fetch user
    db_user = db.query(user_models.User).filter(user_models.User.email == user.email).first()

    if not db_user or not db_user.hashed_password or not utils.verify_password(user.password, db_user.hashed_password):
        # record failed attempt async
        await record_failed_attempt(ip=ip, identifier=identifier, redis=redis, request=request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Successful login: reset attempts
    await reset_attempts(ip=ip, identifier=identifier, redis=redis)

    # Create tokens
    access_token = utils.create_access_token(subject=db_user.id)
    
    # Create refresh token and store in DB hashed
    raw_refresh = utils.create_refresh_token(subject=db_user.id)
    hashed = utils.hash_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=utils.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        user_id=db_user.id,
        token_hash=hashed,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None
    )
    db.add(rt)
    db.commit()

    # Set cookie httpOnly + Secure
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh,
        httponly=True,
        secure=False, # Set to True in production with HTTPS
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
        expires=int((expires_at - datetime.now(timezone.utc)).total_seconds())
    )

    return {"access_token": access_token, "token_type": "bearer"}


"""
OAuth Login (Google, Apple, etc)
"""
@router.post("/oauth/{provider}", response_model=user_schema.Token)
def oauth_login(provider: str, token: str, db: Session = Depends(get_db)):
    # provider: Google or Apple
    # token: get id by the frontend

    if provider == "google":
        user_info = verify_google_token(token)
    # elif provider == "apple":
    #     user_info = verify_apple_token(token)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")
    
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

    # Generate token
    access_token = utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=user_schema.Token)
def refresh_token(response: Response, request: Request, db: Session = Depends(get_db), refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME)):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    # Hash and verify in DB
    hashed = utils.hash_token(refresh_token)
    db_rt = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed).first()
    if not db_rt or db_rt.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if db_rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    
    # Generate new access token and rotate refresh token
    user = db.get(user_models.User, db_rt.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    db_rt.revoked = True
    new_access = utils.create_access_token(subject=user.id)

    # Rotate: create new refresh token, mark old as revoked
    raw_new_refresh = utils.create_refresh_token(subject=user.id)
    new_hash = utils.hash_token(raw_new_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=utils.REFRESH_TOKEN_EXPIRE_DAYS)

    new_db_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None
    )

    db.add(new_db_rt)
    db.commit()

    # Rewrite cookie
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_new_refresh,
        httponly=True,
        secure=False, # Set to True in production with HTTPS
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
        expires=int((expires_at - datetime.now(timezone.utc)).total_seconds())
    )

    return {"access_token": new_access, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response, refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME), db: Session = Depends(get_db)):
    if refresh_token:
        hashed = utils.hash_token(refresh_token)
        db_rt = db.query(RefreshToken).filter(RefreshToken.token_hash == hashed).first()
        if db_rt:
            db_rt.revoked = True
            db.add(db_rt)
            db.commit()

    # Remove cookie from client
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    return {"detail": "Logged out successfully"}

@router.get("/me")
def get_me(current_user: user_models.User = Depends(utils.get_current_user)):
    # Return current user info by jwt token
    return current_user