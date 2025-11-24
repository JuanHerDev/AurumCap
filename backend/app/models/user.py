from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base
from typing import TYPE_CHECKING
import enum

# For type-checkers / IDEs only (prevents runtime circular import)
if TYPE_CHECKING:
    from app.models.investment import Investment  # noqa: F401

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
    hashed_password = Column(String, nullable=True)  # It could be null for Google or Apple sign-ins
    full_name = Column(String, nullable=True)
    auth_provider = Column(Enum(AuthProviderEnum, native_enum=False), default=AuthProviderEnum.local, nullable=False)
    picture_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole, native_enum=False), default=UserRole.investor, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


    # Relationship with tokens
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Use fully-qualified string for Investment to avoid import-order issues
    investments = relationship(
        "app.models.investment.Investment",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
   )

    # Properties for role checks
    @property
    def is_admin(self):
        """Verify if the user is admin"""
        return self.role == UserRole.admin
    
    @property
    def is_analyst(self):
        """Verify if the user is analyst"""
        return self.role in [UserRole.admin, UserRole.analyst]
    
    @property
    def is_support(self):
        """Verify if the user is support"""
        return self.role in [UserRole.admin, UserRole.support]
    
    @property
    def is_superuser(self):
        """Alias for is_admin"""
        return self.is_admin
    
    def has_role(self, required_role: UserRole):
        """
        Verify if user has at least the required role
        """
        role_hierarchy = {
            UserRole.investor: 0,
            UserRole.support: 1,
            UserRole.analyst: 2,
            UserRole.admin: 3
        }
        return role_hierarchy[self.role] >= role_hierarchy[required_role]