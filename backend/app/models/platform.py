from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    type = Column(String)

    country = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="platform")