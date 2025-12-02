from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class AlertType(str, Enum):
    PRICE_TARGET = "price_target"
    PERCENT_CHANGE = "percent_change"
    MOVING_AVERAGE = "moving_average"
    VOLUME_SPIKE = "volume_spike"

class TriggerDirection(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    BOTH = "both"

class PriceAlertBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    asset_type: str = Field(..., min_length=1, max_length=20)
    alert_type: AlertType
    investment_id: Optional[int] = None
    
    # Conditional fields based on alert_type
    target_price: Optional[float] = None
    percent_change: Optional[float] = None
    current_price: float = Field(..., gt=0)
    trigger_direction: TriggerDirection = Field(default=TriggerDirection.BOTH)
    
    expiration_date: Optional[datetime] = None
    name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    
    # Notification settings
    notify_email: bool = Field(default=True)
    notify_push: bool = Field(default=True)
    notify_sms: bool = Field(default=False)

    @model_validator(mode='after')
    def validate_alert_conditions(self):
        if self.alert_type == AlertType.PRICE_TARGET and not self.target_price:
            raise ValueError("target_price is required for price_target alerts")
        if self.alert_type == AlertType.PERCENT_CHANGE and not self.percent_change:
            raise ValueError("percent_change is required for percent_change alerts")
        if self.expiration_date and self.expiration_date <= datetime.now():
            raise ValueError("expiration_date must be in the future")
        return self

class PriceAlertCreate(PriceAlertBase):
    user_id: Optional[int] = None

class PriceAlertUpdate(BaseModel):
    target_price: Optional[float] = None
    percent_change: Optional[float] = None
    current_price: Optional[float] = None
    trigger_direction: Optional[TriggerDirection] = None
    expiration_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    notify_email: Optional[bool] = None
    notify_push: Optional[bool] = None
    notify_sms: Optional[bool] = None

class PriceAlertOut(PriceAlertBase):
    id: int
    user_id: int
    is_active: bool
    triggered: bool
    triggered_at: Optional[datetime]
    triggered_price: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True