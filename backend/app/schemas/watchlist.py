from pydantic import BaseModel


class WatchlistAddRequest(BaseModel):
    asset_id: int


class WatchlistItem(BaseModel):
    asset_id: int
    symbol: str
    name: str
    asset_type: str
    current_price: float | None = None
    change_pct: float | None = None


class WatchlistResponse(BaseModel):
    user_id: int
    items: list[WatchlistItem]
    total: int