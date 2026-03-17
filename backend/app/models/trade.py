from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))

    direction = Column(String)

    entry_price = Column(Float)
    exit_price = Column(Float)

    size = Column(Float)

    entry_date = Column(DateTime)
    exit_date = Column(DateTime)

    strategy = Column(String)

    notes = Column(String)

    asset = relationship("Asset", back_populates="trades")