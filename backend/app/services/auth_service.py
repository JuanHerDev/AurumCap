from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import bcrypt
import jwt

from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.settings import settings



# Private helpers


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")



# Public services


async def register_user(data: RegisterRequest, db: AsyncSession) -> TokenResponse:

    # First, verify that the email is not registered.
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Second, create the user
    user = User(
        email=data.email,
        password_hash=_hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()    # flush to get the id without closing the transaction

    return TokenResponse(access_token=_create_token(user.id))


async def login_user(data: LoginRequest, db: AsyncSession) -> TokenResponse:

    # First, find the user by email
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    # Same error for email not found and incorrect password
    # — avoid listing registered users
    if not user or not _verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(access_token=_create_token(user.id))