from pydantic import BaseModel
from datetime import datetime


class AssetBase(BaseModel):
    symbol: str
    name: str
    asset_type: str             # "stock" | "etf" | "crypto"
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None
    description: str | None = None


class AssetResponse(AssetBase):
    id: int

    model_config = {"from_attributes": True}


class AssetDetailResponse(AssetBase):
    id: int
    market_cap: float | None = None
    logo: str | None = None
    website: str | None = None
    ipo_date: str | None = None
    currency: str | None = None

    model_config = {"from_attributes": True}