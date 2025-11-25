from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    broker = "broker"
    exchange = "exchange"
    bank = "bank"
    wallet = "wallet"
    other = "other"

# Base schema
class PlatformBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=255)
    type: PlatformType
    is_active: bool = True
    supported_asset_types: List[str] = Field(default_factory=list)
    api_config: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None

# Output schema
class PlatformOut(PlatformBase):
    id: int
    created_at: datetime
    updated_at: datetime

# Create schema
class PlatformCreate(PlatformBase):
    pass

# Update schema  
class PlatformUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    display_name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=255)
    type: Optional[PlatformType] = None
    is_active: Optional[bool] = None
    supported_asset_types: Optional[List[str]] = None
    api_config: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None

# Schema with statistics
class PlatformWithStats(PlatformOut):
    investment_count: int
    total_invested: float