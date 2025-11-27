# app/models/historic.py

from sqlalchemy import Column, String, Integer, BigInteger, Float, Text, Boolean, Date, DateTime, Time, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


# ==================== 🪙 CRYPTO TABLES ====================

class CryptoProfile(Base):
    __tablename__ = "crypto_profiles"
    
    id = Column(String(100), primary_key=True)  # CoinGecko ID
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description_es = Column(Text)
    description_en = Column(Text)
    website = Column(String(500))
    whitepaper_url = Column(String(500))
    github_url = Column(String(500))
    categories = Column(JSON)  # ["defi", "smart-contracts"]
    market_cap_rank = Column(Integer)
    logo_url = Column(String(500))
    tags = Column(JSON)  # ["mineable", "pow", "store-of-value"]
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)  # 30 días
    
    __table_args__ = (
        Index('idx_crypto_symbol', 'symbol'),
        Index('idx_crypto_cache', 'cache_until'),
    )

class CryptoSymbolMapping(Base):
    __tablename__ = "crypto_symbol_mapping"
    
    symbol = Column(String(20), primary_key=True)  # "btc", "eth"
    coingecko_id = Column(String(100), nullable=False)  # "bitcoin", "ethereum"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_crypto_mapping_active', 'is_active'),
    )

class CryptoCategory(Base):
    __tablename__ = "crypto_categories"
    
    category_id = Column(String(50), primary_key=True)  # "defi", "nft", "gaming"
    name_es = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# ==================== 🏢 STOCKS TABLES ====================

class StockProfile(Base):
    __tablename__ = "stock_profiles"
    
    symbol = Column(String(20), primary_key=True)  # "AAPL", "TSLA"
    company_name = Column(String(200), nullable=False)
    description = Column(Text)
    sector = Column(String(100))  # "Technology"
    industry = Column(String(100))  # "Consumer Electronics"
    country = Column(String(50))  # "US"
    currency = Column(String(10))  # "USD"
    exchange = Column(String(20))  # "NASDAQ"
    market_cap = Column(BigInteger)  # Para referencia
    employees = Column(Integer)
    website = Column(String(500))
    logo_url = Column(String(500))
    ipo_date = Column(Date)
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)  # 90 días
    
    __table_args__ = (
        Index('idx_stock_sector', 'sector'),
        Index('idx_stock_industry', 'industry'),
        Index('idx_stock_cache', 'cache_until'),
    )

class StockSector(Base):
    __tablename__ = "stock_sectors"
    
    sector_id = Column(String(50), primary_key=True)  # "technology", "healthcare"
    sector_name = Column(String(100), nullable=False)
    description = Column(Text)
    typical_pe_ratio = Column(Float)  # Ratios típicos del sector
    typical_dividend_yield = Column(Float)
    typical_roe = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

class StockIndustry(Base):
    __tablename__ = "stock_industries"
    
    industry_id = Column(String(50), primary_key=True)  # "consumer-electronics"
    industry_name = Column(String(100), nullable=False)
    sector_id = Column(String(50), ForeignKey('stock_sectors.sector_id'), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    sector = relationship("StockSector", backref="industries")

class StockExchange(Base):
    __tablename__ = "stock_exchanges"
    
    exchange_code = Column(String(10), primary_key=True)  # "NASDAQ", "NYSE"
    exchange_name = Column(String(100), nullable=False)
    country = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)
    opening_time = Column(Time)  # Horario local
    closing_time = Column(Time)
    timezone = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)


# ==================== 📈 FUNDAMENTALES - ACTUAL ====================

class StockFundamentalsCurrent(Base):
    __tablename__ = "stock_fundamentals_current"
    
    symbol = Column(String(20), primary_key=True)
    # Métricas clave actuales
    pe_ratio = Column(Float)
    eps = Column(Float)
    dividend_yield = Column(Float)
    market_cap = Column(BigInteger)
    revenue = Column(BigInteger)
    net_income = Column(BigInteger)
    profit_margin = Column(Float)
    # Balance sheet actual
    total_assets = Column(BigInteger)
    total_liabilities = Column(BigInteger)
    cash = Column(BigInteger)
    # Datos de referencia
    year_high = Column(Float)
    year_low = Column(Float)
    volume_avg = Column(BigInteger)
    # Fechas importantes
    last_earnings_date = Column(Date)
    next_earnings_date = Column(Date)
    fiscal_year_end = Column(String(20))  # "September", "December"
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)  # 7 días
    
    __table_args__ = (
        Index('idx_fundamentals_cache', 'cache_until'),
    )

class SectorMetrics(Base):
    __tablename__ = "sector_metrics"
    
    sector = Column(String(100), primary_key=True)
    # Ratios promedio del sector
    avg_pe_ratio = Column(Float)
    avg_ps_ratio = Column(Float)  # Price to Sales
    avg_pb_ratio = Column(Float)  # Price to Book
    avg_debt_to_equity = Column(Float)
    avg_roe = Column(Float)  # Return on Equity
    avg_profit_margin = Column(Float)
    avg_dividend_yield = Column(Float)
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)  # 30 días

# ==================== 🗃️ FUNDAMENTALES - HISTÓRICO ====================

class StockFundamentalsHistorical(Base):
    __tablename__ = "stock_fundamentals_historical"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    period_type = Column(String(10), nullable=False)  # "quarterly", "annual"
    fiscal_date = Column(Date, nullable=False)  # Fecha del reporte
    report_date = Column(Date)  # Cuándo se publicó
    
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
    
    # RATIOS (calculados)
    pe_ratio = Column(Float)
    ps_ratio = Column(Float)  # Price to Sales
    pb_ratio = Column(Float)  # Price to Book
    roe = Column(Float)  # Return on Equity
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    profit_margin = Column(Float)
    
    # METADATA
    shares_outstanding = Column(BigInteger)
    market_cap = Column(BigInteger)  # En la fecha del reporte
    source = Column(String(50))  # "finnhub", "twelvedata"
    is_estimated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # ÍNDICES COMPUESTOS para búsquedas rápidas
    __table_args__ = (
        Index('idx_historical_symbol_fiscal', 'symbol', 'fiscal_date'),
        Index('idx_historical_symbol_period', 'symbol', 'period_type'),
        Index('idx_historical_fiscal_range', 'fiscal_date'),
    )

# ==================== 🌍 DATOS MACROECONÓMICOS ====================

class EconomicData(Base):
    __tablename__ = "economic_data"
    
    indicator_code = Column(String(50), primary_key=True)  # "GDP", "CPI", "UNRATE"
    indicator_name = Column(String(200), nullable=False)
    country = Column(String(50), nullable=False)
    frequency = Column(String(20))  # "monthly", "quarterly", "annual"
    current_value = Column(Float)
    previous_value = Column(Float)
    unit = Column(String(50))  # "percent", "index", "currency"
    last_update_date = Column(Date, nullable=False)
    next_update_date = Column(Date)  # Para saber cuándo refrescar
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)  # Hasta next_update_date
    
    __table_args__ = (
        Index('idx_economic_country', 'country'),
        Index('idx_economic_frequency', 'frequency'),
        Index('idx_economic_cache', 'cache_until'),
    )

class EconomicCalendarCache(Base):
    __tablename__ = "economic_calendar_cache"
    
    event_id = Column(String(100), primary_key=True)
    event_name = Column(String(200), nullable=False)
    country = Column(String(50), nullable=False)
    importance = Column(String(10))  # "low", "medium", "high"
    event_date = Column(DateTime, nullable=False)
    actual_value = Column(Float)
    forecast_value = Column(Float)
    previous_value = Column(Float)
    last_updated = Column(DateTime, default=datetime.now)
    cache_strategy = Column(String(20))  # "past_events", "upcoming"
    
    __table_args__ = (
        Index('idx_calendar_country_date', 'country', 'event_date'),
        Index('idx_calendar_importance', 'importance'),
        Index('idx_calendar_strategy', 'cache_strategy'),
    )

# ==================== 🏛️ PLATAFORMAS/BROKERS ====================

class TradingPlatform(Base):
    __tablename__ = "trading_platforms"
    
    platform_id = Column(String(50), primary_key=True)  # "binance", "coinbase", "etoro"
    name = Column(String(100), nullable=False)
    type = Column(String(20))  # "cex", "dex", "broker"
    supported_assets = Column(JSON)  # ["crypto", "stocks", "forex"]
    website = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_platform_type', 'type'),
        Index('idx_platform_active', 'is_active'),
    )

# ==================== 📊 TRADING TABLES ====================

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # "DCA", "Swing Trading", "Momentum"
    description = Column(Text)
    strategy_type = Column(String(50))  # "technical", "fundamental", "hybrid"
    risk_level = Column(String(20))  # "low", "medium", "high"
    time_frame = Column(String(20))  # "intraday", "swing", "long_term"
    supports_shorting = Column(Boolean, default=False)  # Nueva: si permite short
    created_at = Column(DateTime, default=datetime.now)
    
    # Relación con trades
    trades = relationship("Trade", back_populates="strategy")


class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    # Relación con la inversión principal
    investment_id = Column(Integer, ForeignKey('investments.id'))
    
    # DATOS DEL ACTIVO
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20))  # "stock", "crypto", "forex"
    
    # TIPO DE POSICIÓN (CORREGIDO)
    position_type = Column(String(10), nullable=False)  # "long", "short"
    
    # ACCIÓN DEL TRADE
    trade_action = Column(String(10), nullable=False)  # "buy", "sell", "short", "cover"
    
    # EJECUCIÓN
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)  # Precio de ejecución
    total_amount = Column(Float, nullable=False)  # quantity * price
    currency = Column(String(10), default="USD")
    
    # ESTRATEGIA Y LÓGICA
    strategy_id = Column(Integer, ForeignKey('trading_strategies.id'))
    reason = Column(Text)  # Por qué se ejecutó el trade
    
    # METADATA
    platform = Column(String(50))  # "binance", "etoro", "interactive_brokers"
    fees = Column(Float, default=0.0)  # Comisiones del trade
    leverage = Column(Float, default=1.0)  # Apalancamiento usado
    trade_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # RELACIONES
    investment = relationship("Investment", backref="trades")
    strategy = relationship("TradingStrategy", back_populates="trades")
    
    __table_args__ = (
        Index('idx_trade_symbol_date', 'symbol', 'trade_date'),
        Index('idx_trade_position_type', 'position_type', 'trade_date'),
        Index('idx_trade_action_type', 'trade_action', 'trade_date'),
        Index('idx_trade_platform', 'platform'),
    )

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20))
    position_type = Column(String(10), nullable=False)  # "long", "short"
    
    # ESTADO ACTUAL DE LA POSICIÓN
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)  # Precio promedio de entrada
    current_price = Column(Float)  # Precio actual del mercado
    unrealized_pnl = Column(Float)  # Ganancia/pérdida no realizada
    unrealized_pnl_percent = Column(Float)  # PnL en porcentaje
    
    # METADATA
    opened_at = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, default=datetime.now)
    is_open = Column(Boolean, default=True, index=True)
    
    __table_args__ = (
        Index('idx_position_symbol_open', 'symbol', 'is_open'),
        Index('idx_position_type_open', 'position_type', 'is_open'),
    )

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    
    # VALORES TOTALES
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_amount = Column(Float, nullable=False)
    total_gain_loss = Column(Float)
    total_roi = Column(Float)
    
    # DESGLOSE POR TIPO DE ACTIVO
    crypto_allocation = Column(Float)  # % en crypto
    stock_allocation = Column(Float)   # % en stocks
    cash_allocation = Column(Float)    # % en efectivo
    
    # POSICIONES LARGOS vs SHORTS (NUEVO)
    long_exposure = Column(Float)  # Valor total en posiciones long
    short_exposure = Column(Float)  # Valor total en posiciones short
    net_exposure = Column(Float)   # long_exposure - short_exposure
    
    # METADATA
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_snapshot_date', 'snapshot_date'),
    )

class PriceAlert(Base):
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20))  # "stock", "crypto"
    alert_type = Column(String(20))  # "price_above", "price_below", "percent_change"
    target_price = Column(Float)
    percent_change = Column(Float)
    current_price = Column(Float)  # Precio cuando se creó la alerta
    is_active = Column(Boolean, default=True)
    triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_alert_symbol_active', 'symbol', 'is_active'),
        Index('idx_alert_triggered', 'triggered'),
    )

class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    indicator_type = Column(String(50))  # "rsi", "macd", "sma_20", "bollinger_bands"
    time_frame = Column(String(20))  # "1h", "4h", "1d", "1w"
    value = Column(Float)
    signal = Column(String(20))  # "bullish", "bearish", "neutral"
    calculated_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_technical_symbol_type', 'symbol', 'indicator_type'),
        Index('idx_technical_calculated', 'calculated_at'),
    )

# ==================== 📈 PERFORMANCE TRACKING ====================

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True)
    metric_date = Column(Date, nullable=False, index=True)
    
    # VALORES DEL PORTFOLIO
    portfolio_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_amount = Column(Float, nullable=False)
    
    # RENDIMIENTOS
    daily_return = Column(Float)  # Retorno del día en %
    daily_return_amount = Column(Float)  # Retorno del día en $
    cumulative_return = Column(Float)  # Retorno acumulado desde inicio en %
    cumulative_return_amount = Column(Float)  # Retorno acumulado en $
    
    # MÉTRICAS DE RIESGO
    volatility = Column(Float)  # Volatilidad anualizada del portfolio (%)
    sharpe_ratio = Column(Float)  # Ratio de Sharpe (risk-adjusted return)
    sortino_ratio = Column(Float)  # Ratio de Sortino (solo volatilidad negativa)
    max_drawdown = Column(Float)  # Máxima caída desde peak (%)
    current_drawdown = Column(Float)  # Drawdown actual (%)
    var_95 = Column(Float)  # Value at Risk al 95% de confianza
    
    # EXPOSICIÓN Y ALCANCAMIENTO
    long_exposure = Column(Float)  # Valor total en posiciones long
    short_exposure = Column(Float)  # Valor total en posiciones short
    net_exposure = Column(Float)   # long_exposure - short_exposure
    gross_exposure = Column(Float)  # long_exposure + short_exposure
    leverage_ratio = Column(Float)  # Apalancamiento total (gross_exposure / portfolio_value)
    
    # ALLOCATION POR ACTIVO
    crypto_allocation = Column(Float)  # % en crypto
    stock_allocation = Column(Float)   # % en stocks
    bond_allocation = Column(Float)    # % en bonos
    cash_allocation = Column(Float)    # % en efectivo
    other_allocation = Column(Float)   # % en otros activos
    
    # ALLOCATION POR SECTOR (solo stocks)
    tech_allocation = Column(Float)
    healthcare_allocation = Column(Float)
    financial_allocation = Column(Float)
    energy_allocation = Column(Float)
    consumer_allocation = Column(Float)
    
    # COMPARATIVAS CON BENCHMARKS (rendimientos diarios en %)
    spy_return = Column(Float)  # S&P 500
    qqq_return = Column(Float)  # NASDAQ 100
    btc_return = Column(Float)  # Bitcoin
    bond_return = Column(Float) # Bonos (AGG)
    
    # MÉTRICAS AVANZADAS
    alpha = Column(Float)  # Alpha vs benchmark (exceso de retorno)
    beta = Column(Float)   # Beta vs benchmark (volatilidad relativa)
    tracking_error = Column(Float)  # Error de seguimiento vs benchmark
    information_ratio = Column(Float)  # Ratio de información
    
    # ESTADÍSTICAS DE TRADING
    total_trades = Column(Integer)  # Total de trades hasta la fecha
    winning_trades = Column(Integer)  # Trades ganadores
    losing_trades = Column(Integer)  # Trades perdedores
    win_rate = Column(Float)  # % de trades ganadores
    avg_winning_trade = Column(Float)  # Ganancia promedio por trade ganador
    avg_losing_trade = Column(Float)  # Pérdida promedio por trade perdedor
    profit_factor = Column(Float)  # (Total ganancias) / (Total pérdidas)
    
    # METADATA
    calculation_method = Column(String(50), default="daily")  # "daily", "weekly", "monthly"
    data_quality_score = Column(Float)  # Score de calidad de datos (0-1)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_performance_date', 'metric_date'),
        Index('idx_performance_returns', 'daily_return', 'cumulative_return'),
        Index('idx_performance_risk', 'volatility', 'sharpe_ratio'),
        Index('idx_performance_drawdown', 'max_drawdown', 'current_drawdown'),
    )

# ==================== 🔧 MIGRATION SCRIPT ACTUALIZADO ====================

def create_cache_tables(engine):
    """Función para crear solo las tablas de cache (sin afectar tablas existentes)"""
    
    # Lista de todos los modelos de cache
    cache_models = [
        CryptoProfile,
        CryptoSymbolMapping,
        CryptoCategory,
        StockProfile,
        StockSector,
        StockIndustry,
        StockExchange,
        StockFundamentalsCurrent,
        SectorMetrics,
        StockFundamentalsHistorical,
        EconomicData,
        EconomicCalendarCache,
        TradingPlatform,
        TradingStrategy,
        Trade,
        Position,
        PortfolioSnapshot,
        PriceAlert,
        TechnicalIndicator,
        PerformanceMetric
    ]
    
    # Crear solo estas tablas
    for model in cache_models:
        model.__table__.create(engine, checkfirst=True)
    
    print("✅ Todas las tablas de cache y trading creadas exitosamente!")
    print(f"📊 Total tablas nuevas: {len(cache_models)}")

# Lista para fácil importación
CACHE_AND_TRADING_MODELS = [
    CryptoProfile,
    CryptoSymbolMapping,
    CryptoCategory,
    StockProfile,
    StockSector,
    StockIndustry,
    StockExchange,
    StockFundamentalsCurrent,
    SectorMetrics,
    StockFundamentalsHistorical,
    EconomicData,
    EconomicCalendarCache,
    TradingPlatform,
    TradingStrategy,
    Trade,
    Position,
    PortfolioSnapshot,
    PriceAlert,
    TechnicalIndicator,
    PerformanceMetric
]