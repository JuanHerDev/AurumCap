from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class PlatformType(str, Enum):
    broker = "broker"
    exchange = "exchange" 
    bank = "bank"
    wallet = "wallet"
    other = "other"

class PlatformBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="Platform name")
    type: PlatformType = Field(default=PlatformType.other, description="Platform type")
    description: Optional[str] = Field(None, max_length=255, description="Platform description")
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class PlatformCreate(PlatformBase):
    pass

class PlatformUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    type: Optional[PlatformType] = Field(None)
    description: Optional[str] = Field(None, max_length=255)
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class PlatformOut(PlatformBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class PlatformWithStats(PlatformOut):
    investment_count: int = Field(0, description="Number of investments using this platform")
    total_invested: Decimal = Field(0, description="Total amount invested through this platform")