from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from dotenv import load_dotenv
import os, secrets, hashlib
from datetime import datetime, timedelta, timezone

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

# Password Managment

def hash_password(password: str) -> str:
    # bcrypt has a maximum password length of 72 bytes
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Token Managment

def create_access_token(
    *, subject: int | str, extra_data: dict | None = None, expires_minutes: int | None = None
) -> str:
    """
    Create a JWT access token.
    Can include extra user data (e.g. from Google).
    """
    to_encode = {"sub": str(subject)}
    
    if extra_data:
        to_encode.update(extra_data)
    
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(subject: int):
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    raw_refresh = secrets.token_urlsafe(32)
    return raw_refresh, expires
    

def hash_token(token: str) -> str:
    # Hash the token with SHA-256 and a secret key
    h = hashlib.sha256()
    h.update(token.encode('utf-8'))
    h.update(SECRET_KEY.encode('utf-8'))
    return h.hexdigest()

def verify_refresh_token_hash(token:str, token_hash:str) -> bool:
    return hash_token(token) == token_hash

def verify_access_token(token: str) -> int:
    """
    Decode and verify a JWT access token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("Invalid token: missing subject")
        return int(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    