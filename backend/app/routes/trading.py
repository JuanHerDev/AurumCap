from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.trading_service import (
    open_trade,
    close_trade,
    get_trades,
    delete_trade,
)
from app.schemas.trading import TradeRequest, TradeCloseRequest, TradeResponse

router = APIRouter(prefix="/trades", tags=["Trading"])


@router.post("", response_model=TradeResponse, status_code=201)
async def open_trade_endpoint(
    data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await open_trade(data, current_user, db)


@router.put("/{trade_id}/close", response_model=TradeResponse)
async def close_trade_endpoint(
    trade_id: int,
    data: TradeCloseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await close_trade(trade_id, data, current_user, db)


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_trades(current_user, db, open_only=False, limit=limit, offset=offset)


@router.get("/open", response_model=list[TradeResponse])
async def list_open_trades(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_trades(current_user, db, open_only=True)


@router.delete("/{trade_id}", status_code=204)
async def delete_trade_endpoint(
    trade_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_trade(trade_id, current_user, db)