from pydantic import BaseModel

class PriceResponse(BaseModel):
    symbol: str
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float
    change_pct: float
    market_status: str  # "open" | "extended-hours" | "closed" | "unknown"

    # Crypto-only (None for stocks/ETFs)
    change_pct_7d: float | None = None
    volume_24h: float | None = None
    market_cap: float | None = None
    rank: int | None = None