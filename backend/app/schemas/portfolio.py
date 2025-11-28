from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class InvestmentCardResponse(BaseModel):
    """Response schema for investment card in portfolio list"""
    id: int
    symbol: str
    asset_name: Optional[str]
    asset_type: str
    quantity: float
    invested_amount: float
    current_price: Optional[float]
    current_value: float
    roi: float
    profit_loss: float
    platform: Optional[str]
    category: Optional[str]
    currency: str

class InvestmentModalResponse(BaseModel):
    """Response schema for investment modal"""
    investment: Dict[str, Any]
    current_price: Optional[float]
    current_value: float
    roi: float
    profit_loss: float
    asset_profile: Dict[str, Any]
    market_data: Dict[str, Any]
    related_news: List[Dict[str, Any]]

class InvestmentDetailResponse(BaseModel):
    """Response schema for investment modal detail"""
    investment: Dict[str, Any]
    current_price: Optional[float]
    current_value: float
    roi: float
    profit_loss: float
    asset_profile: Dict[str, Any]
    market_data: Dict[str, Any]
    related_news: List[Dict[str, Any]]

class PortfolioSummaryResponse(BaseModel):
    """Response schema for portfolio summary"""
    total_invested: float
    total_current_value: float
    total_roi: float
    total_profit_loss: float
    investments: List[InvestmentCardResponse]
    investment_count: int
    last_updated: datetime

class AllocationResponse(BaseModel):
    """Response schema for portfolio allocations"""
    by_asset_type: Dict[str, float]
    by_platform: Dict[str, float]
    by_category: Dict[str, float]

class PerformanceResponse(BaseModel):
    """Response schema for performance metrics"""
    total_roi: float
    total_profit_loss: float
    total_invested: float
    total_current_value: float
    investment_count: int
    allocations: AllocationResponse
    best_performer: Optional[Dict[str, Any]]
    worst_performer: Optional[Dict[str, Any]]