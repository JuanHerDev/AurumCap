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
from sqlalchemy.sql import func
from app.db.database import Base
from datetime import datetime  # ✅ SOLO datetime, SIN timezone
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

    # ✅ CORREGIDO: DateTime SIN timezone=True y usando func.now() para consistencia
    date_acquired = Column(
        DateTime,  # ❌ ELIMINAR: timezone=True
        server_default=func.now(),
        nullable=True,
    )

    created_at = Column(
        DateTime,  # ❌ ELIMINAR: timezone=True
        server_default=func.now(),  # ✅ Usar server_default en lugar de lambda
        nullable=False,
    )

    updated_at = Column(
        DateTime,  # ❌ ELIMINAR: timezone=True
        server_default=func.now(),  # ✅ Usar server_default
        onupdate=func.now(),  # ✅ Usar func.now() en lugar de lambda
        nullable=False,
    )

    user = relationship("User", back_populates="investments", passive_deletes=True)
    platform = relationship("Platform", back_populates="investments", passive_deletes=True)

    def __init__(self, **kwargs):
        """
        Constructor personalizado para asegurar que los timestamps se establezcan correctamente
        """
        # ✅ Asegurar que los timestamps tengan valores si no se proporcionan
        from datetime import datetime
        
        # Si date_acquired no se proporciona, usar None (la BD usará server_default)
        if 'date_acquired' not in kwargs:
            kwargs['date_acquired'] = None
            
        # created_at y updated_at se manejan automáticamente por server_default
        # No necesitamos establecerlos aquí
        
        super().__init__(**kwargs)
    
    def to_dict(self):
        """
        Método auxiliar para convertir a dict evitando problemas de serialización
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform_id": self.platform_id,
            "asset_type": self.asset_type.value if self.asset_type else None,
            "symbol": self.symbol,
            "coingecko_id": self.coingecko_id,
            "twelvedata_id": self.twelvedata_id,
            "asset_name": self.asset_name,
            "invested_amount": float(self.invested_amount) if self.invested_amount else None,
            "quantity": float(self.quantity) if self.quantity else None,
            "purchase_price": float(self.purchase_price) if self.purchase_price else None,
            "currency": self.currency.value if self.currency else None,
            "date_acquired": self.date_acquired.isoformat() if self.date_acquired else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }