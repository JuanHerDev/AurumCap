from sqlalchemy import Column, String, Integer, BigInteger, Text, Date, DateTime, Time, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class StockProfile(Base):
    __tablename__ = "stock_profiles"
    
    symbol = Column(String(20), primary_key=True)
    company_name = Column(String(200), nullable=False)
    description = Column(Text)
    sector = Column(String(100))
    industry = Column(String(100))
    country = Column(String(50))
    currency = Column(String(10))
    exchange = Column(String(20))
    market_cap = Column(BigInteger)
    employees = Column(Integer)
    website = Column(String(500))
    logo_url = Column(String(500))
    ipo_date = Column(Date)
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)

class StockSector(Base):
    __tablename__ = "stock_sectors"
    
    sector_id = Column(String(50), primary_key=True)
    sector_name = Column(String(100), nullable=False)
    description = Column(Text)
    typical_pe_ratio = Column(Float)
    typical_dividend_yield = Column(Float)
    typical_roe = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

class StockIndustry(Base):
    __tablename__ = "stock_industries"
    
    industry_id = Column(String(50), primary_key=True)
    industry_name = Column(String(100), nullable=False)
    sector_id = Column(String(50), ForeignKey('stock_sectors.sector_id'), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    sector = relationship("StockSector", backref="industries")

class StockExchange(Base):
    __tablename__ = "stock_exchanges"
    
    exchange_code = Column(String(10), primary_key=True)
    exchange_name = Column(String(100), nullable=False)
    country = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)
    opening_time = Column(Time)
    closing_time = Column(Time)
    timezone = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)