from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class RiskProfileType(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class RiskProfileBase(BaseModel):
    profile_type: RiskProfileType = Field(default=RiskProfileType.MODERATE)
    target_allocations: Dict[str, float] = Field(
        default={
            "crypto": 20.0,
            "stocks": 60.0,
            "bonds": 15.0,
            "cash": 5.0
        }
    )
    max_single_position: float = Field(default=15.0, ge=1.0, le=100.0)
    max_sector_exposure: float = Field(default=30.0, ge=1.0, le=100.0)
    min_diversification_score: float = Field(default=70.0, ge=0.0, le=100.0)
    rebalance_threshold: float = Field(default=5.0, ge=0.1, le=50.0)

    @field_validator('target_allocations')
    def validate_allocations(cls, v):
        total = sum(v.values())
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Target allocations must sum to 100%, got {total}%")
        return v

class RiskProfileCreate(RiskProfileBase):
    user_id: Optional[int] = None

class RiskProfileUpdate(BaseModel):
    profile_type: Optional[RiskProfileType] = None
    target_allocations: Optional[Dict[str, float]] = None
    max_single_position: Optional[float] = None
    max_sector_exposure: Optional[float] = None
    min_diversification_score: Optional[float] = None
    rebalance_threshold: Optional[float] = None

class RiskProfileOut(RiskProfileBase):
    id: int
    user_id: int
    last_rebalanced: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True