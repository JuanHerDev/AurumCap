from pydantic import BaseModel
from datetime import datetime


class HoldingItem(BaseModel):
    asset_id: int
    symbol: str
    name: str
    asset_type: str
    quantity: float
    avg_price: float
    current_price: float
    current_value: float        # quantity × current_price
    total_invested: float       # quantity × avg_price
    pnl: float                  # current_value - total_invested
    pnl_pct: float              # pnl / total_invested × 100
    allocation_pct: float       # % of total portfolio value


class PortfolioResponse(BaseModel):
    user_id: int
    total_value: float
    total_invested: float
    total_pnl: float
    total_pnl_pct: float
    holdings: list[HoldingItem]
    last_updated: datetime