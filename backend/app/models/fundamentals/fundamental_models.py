from sqlalchemy import Column, String, Integer, BigInteger, Float, Date, DateTime, Boolean, Index
from datetime import datetime
from app.db.database import Base

class StockFundamentalsCurrent(Base):
    __tablename__ = "stock_fundamentals_current"
    
    symbol = Column(String(20), primary_key=True)
    pe_ratio = Column(Float)
    eps = Column(Float)
    dividend_yield = Column(Float)
    market_cap = Column(BigInteger)
    revenue = Column(BigInteger)
    net_income = Column(BigInteger)
    profit_margin = Column(Float)
    total_assets = Column(BigInteger)
    total_liabilities = Column(BigInteger)
    cash = Column(BigInteger)
    year_high = Column(Float)
    year_low = Column(Float)
    volume_avg = Column(BigInteger)
    last_earnings_date = Column(Date)
    next_earnings_date = Column(Date)
    fiscal_year_end = Column(String(20))
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)

class SectorMetrics(Base):
    __tablename__ = "sector_metrics"
    
    sector = Column(String(100), primary_key=True)
    avg_pe_ratio = Column(Float)
    avg_ps_ratio = Column(Float)
    avg_pb_ratio = Column(Float)
    avg_debt_to_equity = Column(Float)
    avg_roe = Column(Float)
    avg_profit_margin = Column(Float)
    avg_dividend_yield = Column(Float)
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)

class StockFundamentalsHistorical(Base):
    __tablename__ = "stock_fundamentals_historical"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    period_type = Column(String(10), nullable=False)
    fiscal_date = Column(Date, nullable=False)
    report_date = Column(Date)
    
    # INCOME STATEMENT
    revenue = Column(BigInteger)
    net_income = Column(BigInteger)
    eps = Column(Float)
    dividends_per_share = Column(Float)
    gross_profit = Column(BigInteger)
    operating_income = Column(BigInteger)
    ebitda = Column(BigInteger)
    
    # BALANCE SHEET
    total_assets = Column(BigInteger)
    total_liabilities = Column(BigInteger)
    cash = Column(BigInteger)
    long_term_debt = Column(BigInteger)
    shareholders_equity = Column(BigInteger)
    
    # RATIOS
    pe_ratio = Column(Float)
    ps_ratio = Column(Float)
    pb_ratio = Column(Float)
    roe = Column(Float)
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    profit_margin = Column(Float)
    
    # METADATA
    shares_outstanding = Column(BigInteger)
    market_cap = Column(BigInteger)
    source = Column(String(50))
    is_estimated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)