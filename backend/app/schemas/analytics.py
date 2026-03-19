from pydantic import BaseModel
from datetime import datetime


class SnapshotPoint(BaseModel):
    date: datetime
    total_value: float
    total_invested: float
    pnl: float
    pnl_pct: float


class PortfolioHistoryResponse(BaseModel):
    user_id: int
    range: str
    snapshots: list[SnapshotPoint]


class AssetAllocationItem(BaseModel):
    symbol: str
    name: str
    asset_type: str
    current_value: float
    allocation_pct: float


class AssetAllocationResponse(BaseModel):
    user_id: int
    total_value: float
    allocations: list[AssetAllocationItem]
