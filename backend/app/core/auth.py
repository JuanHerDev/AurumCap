# app/core/auth.py

import os
import time
import logging
from typing import Optional

from jose import jwt, JWTError
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer

import httpx
from dotenv import load_dotenv

from app.models.user import User
from app.crud.user import get_user_by_email
from app.core.redis_client import get_redis

load_dotenv()
logger = logging.getLogger("app.auth")

# ============================================================
# CONFIG
# ============================================================

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ============================================================
# JWT CREATION & VALIDATION
# ============================================================

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    """
    Crea un JWT firmado. Incluye `exp` como UNIX timestamp.
    """
    to_encode = data.copy()
    expire = time.time() + (expires_minutes * 60)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """
    Valida JWT y devuelve payload.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user(
    token: str = Depends(OAUTH2_SCHEME),
    redis=Depends(get_redis),
) -> User:
    """
    Obtiene el usuario autenticado usando JWT + Redis.
    """
    payload = verify_access_token(token)

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Verificar sesión en Redis
    session_key = f"session:{email}"
    exists = await redis.exists(session_key)
    if not exists:
        raise HTTPException(
            status_code=401, detail="Session expired or logged out"
        )

    # Obtener usuario DB
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# ============================================================
# GOOGLE OAUTH UTILITIES
# ============================================================

def build_google_oauth_url():
    """
    URL donde el usuario se autentica con Google.
    """
    base = "https://accounts.google.com/o/oauth2/v2/auth"

    url = (
        f"{base}?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return url


async def exchange_google_code_for_token(code: str) -> dict:
    """
    Intercambia el código por acces_token y id_token.
    """
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(token_url, data=data)
        r.raise_for_status()
        return r.json()


async def verify_google_id_token(id_token: str) -> dict:
    """
    Valida el id_token de Google y devuelve los datos del usuario.
    """
    google_info_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"

    async with httpx.AsyncClient() as client:
        r = await client.get(google_info_url)
        r.raise_for_status()

    info = r.json()

    if info.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    return {
        "email": info["email"],
        "name": info.get("name"),
        "picture": info.get("picture"),
        "email_verified": info.get("email_verified", "false") == "true",
    }

# ============================================================
# SESSION MANAGEMENT
# ============================================================

async def create_user_session(email: str, redis) -> None:
    """
    Registra una sesión en Redis.
    """
    session_key = f"session:{email}"
    await redis.set(session_key, "1", ex=60 * 60 * 24 * 7)  # 7 días


async def destroy_user_session(email: str, redis) -> None:
    """
    Cierra la sesión del usuario.
    """
    session_key = f"session:{email}"
    await redis.delete(session_key)

