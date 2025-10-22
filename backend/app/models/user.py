from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class AuthProviderEnum(enum.Enum):
    local = "local"
    google = "google"
    apple = "apple"

class User(Base):
    __tablename__= 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) # It could be null for Google or Apple sign-ins
    full_name = Column(String, nullable=True)
    auth_provider = Column(Enum(AuthProviderEnum), default=AuthProviderEnum.local, nullable=False) # local, google, apple, etc.
    picture_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())