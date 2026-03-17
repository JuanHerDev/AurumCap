from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from datetime import datetime
from app.db.base import Base

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    date = Column(DateTime, default=datetime.utcnow)

    total_value = Column(Float)
    total_invested = Column(Float)

    pnl = Column(Float)