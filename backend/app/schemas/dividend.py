from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class DividendBase(BaseModel):
    investment_id: int = Field(..., gt=0)
    amount_per_share: float = Field(..., gt=0)
    total_shares: float = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payment_date: datetime
    ex_dividend_date: datetime
    record_date: Optional[datetime] = None
    declared_date: Optional[datetime] = None
    tax_withheld: float = Field(default=0.0, ge=0)
    tax_rate: float = Field(default=0.0, ge=0, le=100)
    reinvested: bool = Field(default=False)
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    
    # Computed field: total_amount (amount_per_share * total_shares)
    # Use @computed_field for calculated properties in Pydantic v2
    @computed_field
    @property
    def total_amount(self) -> float:
        """Calculate total dividend amount (amount_per_share * total_shares)"""
        return self.amount_per_share * self.total_shares
    
    # Computed field: net_amount (total_amount - tax_withheld)
    @computed_field
    @property
    def net_amount(self) -> float:
        """Calculate net dividend amount after tax withholding"""
        return self.total_amount - self.tax_withheld

class DividendCreate(DividendBase):
    user_id: Optional[int] = None

class DividendUpdate(BaseModel):
    amount_per_share: Optional[float] = None
    total_shares: Optional[float] = None
    payment_date: Optional[datetime] = None
    tax_withheld: Optional[float] = None
    tax_rate: Optional[float] = None
    reinvested: Optional[bool] = None
    paid: Optional[bool] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None

class DividendOut(DividendBase):
    id: int
    user_id: int
    # Note: total_amount and net_amount are already computed fields in DividendBase
    paid: bool
    reinvestment_price: Optional[float]
    reinvestment_shares: Optional[float]
    source: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True