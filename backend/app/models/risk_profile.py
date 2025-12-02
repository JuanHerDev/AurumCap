from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum

class RiskProfileType(str, enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class RiskProfile(Base):
    __tablename__ = "risk_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    profile_type = Column(Enum(RiskProfileType), nullable=False, default=RiskProfileType.MODERATE)
    
    # Target allocations in percentage
    target_allocations = Column(JSON, nullable=False, default={
        "crypto": 20.0,
        "stocks": 60.0,
        "bonds": 15.0,
        "cash": 5.0
    })
    
    # Risk tolerance parameters
    max_single_position = Column(Float, default=15.0)  # Max % in single asset
    max_sector_exposure = Column(Float, default=30.0)  # Max % in single sector
    min_diversification_score = Column(Float, default=70.0)  # 0-100 score
    
    # Rebalancing rules
    rebalance_threshold = Column(Float, default=5.0)  # % deviation to trigger rebalance
    last_rebalanced = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())