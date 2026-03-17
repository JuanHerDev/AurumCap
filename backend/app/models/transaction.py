from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"))

    type = Column(String, nullable=False) # BUY SELL

    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    fees = Column(Float, default=0)

    date = Column(DateTime, default=datetime.utcnow)

    notes = Column(String)

    user = relationship("User", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")
    platform = relationship("Platform", back_populates="transactions")