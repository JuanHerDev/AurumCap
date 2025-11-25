from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    DateTime,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func
from datetime import datetime, timezone
import enum

# ENUMS
class PlatformType(str, enum.Enum):
    broker = "broker"
    exchange = "exchange"
    bank = "bank"
    wallet = "wallet"
    other = "other"

class AssetType(str, enum.Enum):
    crypto = "crypto"
    stock = "stock"
    etf = "etf"
    bond = "bond"
    real_estate = "real_estate"
    other = "other"

# PLATFORM MODEL
class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(128), nullable=False, unique=True, index=True)
    display_name = Column(String(128), nullable=False)
    description = Column(String(255), nullable=True)

    type = Column(
        Enum(PlatformType, native_enum=False),
        nullable=False,
        default=PlatformType.other,
    )


    is_active = Column(Boolean, default=True, nullable=False)
    supported_asset_types = Column(JSON, nullable=False, default=list) 
    api_config = Column(JSON, nullable=True)  
    icon = Column(String(255), nullable=True)  

    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship with Investment
    investments = relationship(
        "Investment",
        back_populates="platform",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        """
        Auxiliar method to convert Platform instance to dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "type": self.type.value if self.type else None,
            "is_active": self.is_active,
            "supported_asset_types": self.supported_asset_types,
            "api_config": self.api_config,
            "icon": self.icon,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }