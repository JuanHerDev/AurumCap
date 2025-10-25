from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base
import enum

# Enum for authentication providers
class AuthProviderEnum(enum.Enum):
    local = "local"
    google = "google"
    apple = "apple"

# Enum for user roles
class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    investor = "investor"
    support = "support"


# User model
class User(Base):
    __tablename__= 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) # It could be null for Google or Apple sign-ins
    full_name = Column(String, nullable=True)
    auth_provider = Column(Enum(AuthProviderEnum), default=AuthProviderEnum.local, nullable=False) # local, google, apple, etc.
    picture_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.investor, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship with tokens
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")