from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.watchlist_service import (
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
)
from app.schemas.watchlist import WatchlistResponse, WatchlistItem

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("", response_model=WatchlistResponse)
async def get_my_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_watchlist(current_user, db)


@router.post("/{symbol}", response_model=WatchlistItem, status_code=201)
async def add_asset(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await add_to_watchlist(symbol, current_user, db)


@router.delete("/{symbol}", status_code=204)
async def remove_asset(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_from_watchlist(symbol, current_user, db)