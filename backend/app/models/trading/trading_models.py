from sqlalchemy import JSON, Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class TradingPlatform(Base):
    __tablename__ = "trading_platforms"
    
    platform_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20))
    supported_assets = Column(JSON)
    website = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50))
    risk_level = Column(String(20))
    time_frame = Column(String(20))
    supports_shorting = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    trades = relationship("Trade", back_populates="strategy")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    investment_id = Column(Integer, ForeignKey('investments.id'))
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20))
    position_type = Column(String(10), nullable=False)
    trade_action = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    strategy_id = Column(Integer, ForeignKey('trading_strategies.id'))
    reason = Column(Text)
    platform = Column(String(50))
    fees = Column(Float, default=0.0)
    leverage = Column(Float, default=1.0)
    trade_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    investment = relationship("Investment", backref="trades")
    strategy = relationship("TradingStrategy", back_populates="trades")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20))
    position_type = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    unrealized_pnl_percent = Column(Float)
    opened_at = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, default=datetime.now)
    is_open = Column(Boolean, default=True, index=True)

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_amount = Column(Float, nullable=False)
    total_gain_loss = Column(Float)
    total_roi = Column(Float)
    crypto_allocation = Column(Float)
    stock_allocation = Column(Float)
    cash_allocation = Column(Float)
    long_exposure = Column(Float)
    short_exposure = Column(Float)
    net_exposure = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

class PriceAlert(Base):
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20))
    alert_type = Column(String(20))
    target_price = Column(Float)
    percent_change = Column(Float)
    current_price = Column(Float)
    is_active = Column(Boolean, default=True)
    triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    indicator_type = Column(String(50))
    time_frame = Column(String(20))
    value = Column(Float)
    signal = Column(String(20))
    calculated_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True)
    metric_date = Column(Date, nullable=False, index=True)
    portfolio_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_amount = Column(Float, nullable=False)
    daily_return = Column(Float)
    daily_return_amount = Column(Float)
    cumulative_return = Column(Float)
    cumulative_return_amount = Column(Float)
    volatility = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float)
    current_drawdown = Column(Float)
    var_95 = Column(Float)
    long_exposure = Column(Float)
    short_exposure = Column(Float)
    net_exposure = Column(Float)
    gross_exposure = Column(Float)
    leverage_ratio = Column(Float)
    crypto_allocation = Column(Float)
    stock_allocation = Column(Float)
    bond_allocation = Column(Float)
    cash_allocation = Column(Float)
    other_allocation = Column(Float)
    tech_allocation = Column(Float)
    healthcare_allocation = Column(Float)
    financial_allocation = Column(Float)
    energy_allocation = Column(Float)
    consumer_allocation = Column(Float)
    spy_return = Column(Float)
    qqq_return = Column(Float)
    btc_return = Column(Float)
    bond_return = Column(Float)
    alpha = Column(Float)
    beta = Column(Float)
    tracking_error = Column(Float)
    information_ratio = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    avg_winning_trade = Column(Float)
    avg_losing_trade = Column(Float)
    profit_factor = Column(Float)
    calculation_method = Column(String(50), default="daily")
    data_quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.now)