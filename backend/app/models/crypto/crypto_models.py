from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base

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
    cache_until = Column(DateTime, nullable=False)

class CryptoSymbolMapping(Base):
    __tablename__ = "crypto_symbol_mapping"
    
    symbol = Column(String(20), primary_key=True)
    coingecko_id = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class CryptoCategory(Base):
    __tablename__ = "crypto_categories"
    
    category_id = Column(String(50), primary_key=True)
    name_es = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)