from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ---- Base model: used by others schemas ----
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    auth_provider: Optional[str] = "local"  # local | google | apple
    picture_url: Optional[str] = None


# ---- Schema to create a local user ----
class UserCreate(UserBase):
    password: str


# ---- Schema for local login ----
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ---- Schema to return user in response ----
class UserResponse(UserBase):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Schema to response tokens ----
class Token(BaseModel):
    access_token: str
    token_type: str
