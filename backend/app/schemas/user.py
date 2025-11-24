from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, Literal
import enum
import re

class AuthProviderEnum(str, enum.Enum):
    local = "local"
    google = "google"
    apple = "apple"

class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    investor = "investor"
    support = "support"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    auth_provider: AuthProviderEnum = AuthProviderEnum.local
    picture_url: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        populate_by_name=True
    )

class UserCreate(UserBase):
    password: str

    @field_validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('email')
    def validate_email_domain(cls, v):
        # Basic email validation - extend as needed
        if v and '..' in v:
            raise ValueError('Invalid email format')
        return v.lower()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(str_to_lower=True)

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    picture_url: Optional[str] = None

    model_config = ConfigDict(extra='forbid')

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v