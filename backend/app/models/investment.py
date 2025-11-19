from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Enum,
)
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime, timezone
from app.schemas.investment import AssetType, CurrencyEnum


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    platform_id = Column(
        Integer,
        ForeignKey("platforms.id", ondelete="SET NULL"),
        nullable=True,
    )

    asset_type = Column(
        Enum(AssetType, native_enum=True),
        nullable=False,
        default=AssetType.other,
    )

    symbol = Column(String(64), nullable=False, index=True)

    coingecko_id = Column(String(128), nullable=True, index=True)
    twelvedata_id = Column(String(128), nullable=True, index=True)

    asset_name = Column(String(255), nullable=True)

    invested_amount = Column(Numeric(18, 6, asdecimal=True), nullable=False)
    quantity = Column(Numeric(28, 10, asdecimal=True), nullable=False)
    purchase_price = Column(Numeric(18, 6, asdecimal=True), nullable=False)

    currency = Column(
        Enum(CurrencyEnum, native_enum=False),
        nullable=False,
        default=CurrencyEnum.USD,
    )

    date_acquired = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="investments", passive_deletes=True)
    platform = relationship("Platform", back_populates="investments", passive_deletes=True)
