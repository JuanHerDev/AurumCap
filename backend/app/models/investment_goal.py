from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Boolean
from sqlalchemy.sql import func
from app.db.database import Base
from .risk_profile import RiskProfileType

class InvestmentGoal(Base):
    __tablename__ = "investment_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    
    # Goal parameters
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime, nullable=False)
    
    # Contribution settings
    monthly_contribution = Column(Float, default=0.0)
    initial_investment = Column(Float, default=0.0)
    
    # Risk profile for this specific goal
    risk_profile = Column(Enum(RiskProfileType), default=RiskProfileType.MODERATE)
    
    # Status
    is_active = Column(Boolean, default=True)
    achieved = Column(Boolean, default=False)
    achievement_date = Column(DateTime)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    months_remaining = Column(Integer)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())