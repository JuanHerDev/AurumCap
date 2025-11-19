from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Hashed token stored in DB
    token_hash = Column(String(256), nullable=False, index=True, unique=True)

    # Expiration date of the refresh token (UTC)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Metadata
    user_agent = Column(String(256), nullable=True)
    ip = Column(String(64), nullable=True)

    # Revoked control
    revoked = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")

    def is_expired(self) -> bool:
        # Check if the token is expired
        return self.expires_at < datetime.now(timezone.utc)