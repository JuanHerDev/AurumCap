from pydantic import BaseModel, field_validator
from datetime import datetime


class TradeRequest(BaseModel):
    asset_id: int
    direction: str              # "long" | "short"
    entry_price: float
    size: float
    entry_date: datetime
    strategy: str | None = None
    notes: str | None = None

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v.lower() not in ("long", "short"):
            raise ValueError("direction must be long or short")
        return v.lower()


class TradeCloseRequest(BaseModel):
    exit_price: float
    exit_date: datetime
    notes: str | None = None


class TradeResponse(BaseModel):
    id: int
    asset_id: int
    symbol: str
    direction: str
    entry_price: float
    exit_price: float | None = None
    size: float
    entry_date: datetime
    exit_date: datetime | None = None
    pnl: float | None = None    # None if the trade still open
    pnl_pct: float | None = None
    strategy: str | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}