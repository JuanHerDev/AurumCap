from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    asset_type = Column(String) # Crypto, Asset, ETF, ETC...

    exchange = Column(String)
    sector = Column(String)
    industry = Column(String)

    description = Column(String)

    search_vector = Column(String)

    transactions = relationship("Transaction", back_populates="asset")
    price_history = relationship("PriceHistory", back_populates="asset")
    trades = relationship("Trade", back_populates="asset")
    news = relationship("News", back_populates="asset")