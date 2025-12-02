from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.database import Base

class Dividend(Base):
    __tablename__ = "dividends"
    
    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Dividend details
    amount_per_share = Column(Float, nullable=False)
    total_shares = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    
    # Payment details
    payment_date = Column(DateTime, nullable=False)
    ex_dividend_date = Column(DateTime, nullable=False)
    record_date = Column(DateTime)
    declared_date = Column(DateTime)
    
    # Tax information
    tax_withheld = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    net_amount = Column(Float, nullable=False)
    
    # Reinvestment
    reinvested = Column(Boolean, default=False)
    reinvestment_price = Column(Float)
    reinvestment_shares = Column(Float)
    
    # Status
    paid = Column(Boolean, default=False)
    payment_method = Column(String(50))  # cash, stock, etc.
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Metadata
    source = Column(String(50))  # manual, api, import
    notes = Column(String(500))