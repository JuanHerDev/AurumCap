from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    DateTime,
)
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime, timezone
import enum



# ENUMS

class PlatformType(str, enum.Enum):
    broker = "broker"
    exchange = "exchange"
    bank = "bank"
    wallet = "wallet"
    other = "other"


# PLATFORM MODEL

class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)

    type = Column(
        Enum(PlatformType, native_enum=False),
        nullable=False,
        default=PlatformType.other,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship with Investment
    investments = relationship(
        "Investment",
        back_populates="platform",
        cascade="all, delete-orphan",
    )
