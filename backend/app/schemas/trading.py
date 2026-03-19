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

    @field_validator("entry_price", "size")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v

    @field_validator("entry_date")
    @classmethod
    def normalize_datetime(cls, v: datetime) -> datetime:
        from datetime import timezone
        if v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class TradeCloseRequest(BaseModel):
    exit_price: float
    exit_date: datetime
    notes: str | None = None

    @field_validator("exit_price")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v

    @field_validator("exit_date")
    @classmethod
    def normalize_datetime(cls, v: datetime) -> datetime:
        from datetime import timezone
        if v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


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
    pnl: float | None = None
    pnl_pct: float | None = None
    is_open: bool
    strategy: str | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}