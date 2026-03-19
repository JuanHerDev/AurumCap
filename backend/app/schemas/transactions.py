from pydantic import BaseModel, field_validator
from datetime import datetime, timezone


class TransactionRequest(BaseModel):
    asset_id: int
    platform_id: int | None = None
    type: str                   # "BUY" | "SELL"
    quantity: float
    price: float
    fees: float = 0.0
    date: datetime
    notes: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v.upper() not in ("BUY", "SELL"):
            raise ValueError("type must be BUY or SELL")
        return v.upper()

    @field_validator("quantity", "price")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v
    
    @field_validator("date")
    @classmethod
    def normalize_date(cls, v: datetime) -> datetime:
        if v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class TransactionResponse(BaseModel):
    id: int
    asset_id: int
    symbol: str
    type: str
    quantity: float
    price: float
    fees: float
    total: float                # quantity × price + fees
    date: datetime
    notes: str | None = None

    model_config = {"from_attributes": True}