from pydantic import BaseModel


class SearchResultItem(BaseModel):
    symbol: str
    name: str
    asset_type: str             # "stock" | "etf" | "crypto"
    exchange: str | None = None
    rank: int | None = None     # Only crypto, None for stocks/ETFs


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total: int