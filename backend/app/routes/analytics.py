from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.analytics_service import (
    get_portfolio_history,
    get_asset_allocation,
    get_benchmark_comparison
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/portfolio/history")
async def portfolio_history(
    range: str = Query(default="1M", description="1D | 1W | 1M | 3M | 1Y | ALL"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_portfolio_history(current_user.id, range, db)

@router.get("/portfolio/allocation")
async def portfolio_allocation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_asset_allocation(current_user.id, db)

@router.get("/portfolio/benchmark")
async def portfolio_benchmark(
    range: str = Query(default="1M", description="1D | 1W | 1M | 3M | 1Y | ALL"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_benchmark_comparison(current_user.id, range, db)