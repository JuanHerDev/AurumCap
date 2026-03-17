from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)

    asset_id = Column(Integer, ForeignKey("assets.id"))

    price = Column(Float, nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow)

    source = Column(String)

    asset = relationship("Asset", back_populates="price_history")