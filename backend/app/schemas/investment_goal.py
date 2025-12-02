from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
from app.models.risk_profile import RiskProfileType

class GoalStatus(str, Enum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    CANCELLED = "cancelled"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"

class InvestmentGoalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    target_amount: float = Field(..., gt=0)
    target_date: datetime
    monthly_contribution: float = Field(default=0.0, ge=0)
    initial_investment: float = Field(default=0.0, ge=0)
    risk_profile: RiskProfileType = Field(default=RiskProfileType.MODERATE)

    @field_validator('target_date')
    def validate_future_date(cls, v):
        if v <= datetime.now():
            raise ValueError("Target date must be in the future")
        return v

class InvestmentGoalCreate(InvestmentGoalBase):
    user_id: Optional[int] = None

class InvestmentGoalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[float] = None
    target_date: Optional[datetime] = None
    monthly_contribution: Optional[float] = None
    initial_investment: Optional[float] = None
    risk_profile: Optional[RiskProfileType] = None
    is_active: Optional[bool] = None

class InvestmentGoalOut(InvestmentGoalBase):
    id: int
    user_id: int
    current_amount: float
    is_active: bool
    achieved: bool
    achievement_date: Optional[datetime]
    progress_percentage: float
    months_remaining: Optional[int]
    status: GoalStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True