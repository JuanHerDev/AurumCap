from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.trade import Trade
from app.models.user import User
from app.providers.twelvedata_provider import twelvedata_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.trading import TradeRequest, TradeCloseRequest, TradeResponse
from app.services.asset_service import get_or_create_asset
import asyncio


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _calculate_pnl(
    direction: str,
    entry_price: float,
    exit_price: float,
    size: float,
) -> tuple[float, float]:
    """
    Returns (pnl, pnl_pct) for a closed trade.
    Long:  profit when exit > entry
    Short: profit when exit < entry
    """
    if direction == "long":
        pnl = (exit_price - entry_price) * size
    else:
        pnl = (entry_price - exit_price) * size

    pnl_pct = (pnl / (entry_price * size) * 100) if entry_price and size else 0.0
    return round(pnl, 4), round(pnl_pct, 4)


async def _fetch_current_price(asset_type: str, symbol: str) -> float | None:
    """Fetches the current price for unrealized P&L calculation."""
    try:
        if asset_type == "crypto":
            data = await coinmarketcap_provider.get_price(symbol)
            return data.price if data else None
        else:
            data = await twelvedata_provider.get_price(symbol)
            return data.price if data else None
    except Exception:
        return None


def _build_trade_response(trade: Trade, symbol: str, current_price: float | None = None) -> TradeResponse:
    """
    Builds a TradeResponse from a Trade model.
    For open trades, calculates unrealized P&L using current price.
    For closed trades, uses the stored exit price and P&L.
    """
    is_open = trade.exit_price is None

    if is_open and current_price:
        pnl, pnl_pct = _calculate_pnl(
            trade.direction,
            trade.entry_price,
            current_price,
            trade.size,
        )
    elif not is_open and trade.exit_price:
        pnl, pnl_pct = _calculate_pnl(
            trade.direction,
            trade.entry_price,
            trade.exit_price,
            trade.size,
        )
    else:
        pnl, pnl_pct = None, None

    return TradeResponse(
        id=trade.id,
        asset_id=trade.asset_id,
        symbol=symbol,
        direction=trade.direction,
        entry_price=trade.entry_price,
        exit_price=trade.exit_price,
        size=trade.size,
        entry_date=trade.entry_date,
        exit_date=trade.exit_date,
        pnl=pnl,
        pnl_pct=pnl_pct,
        is_open=is_open,
        strategy=trade.strategy,
        notes=trade.notes,
    )


# ------------------------------------------------------------------
# Services
# ------------------------------------------------------------------

async def open_trade(
    data: TradeRequest,
    user: User,
    db: AsyncSession,
) -> TradeResponse:
    """Opens a new trade position."""

    # Get or create the asset
    asset = await get_or_create_asset(str(data.asset_id), db) \
        if isinstance(data.asset_id, str) \
        else await _get_asset_by_id(data.asset_id, db)

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    trade = Trade(
        user_id=user.id,
        asset_id=asset.id,
        direction=data.direction,
        entry_price=data.entry_price,
        size=data.size,
        entry_date=data.entry_date,
        strategy=data.strategy,
        notes=data.notes,
    )
    db.add(trade)
    await db.flush()

    # Fetch current price for unrealized P&L
    current_price = await _fetch_current_price(asset.asset_type, asset.symbol)

    return _build_trade_response(trade, asset.symbol, current_price)


async def close_trade(
    trade_id: int,
    data: TradeCloseRequest,
    user: User,
    db: AsyncSession,
) -> TradeResponse:
    """Closes an open trade position with an exit price."""

    result = await db.execute(
        select(Trade).where(
            Trade.id == trade_id,
            Trade.user_id == user.id,
        )
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.exit_price is not None:
        raise HTTPException(status_code=400, detail="Trade is already closed")

    trade.exit_price = data.exit_price
    trade.exit_date = data.exit_date
    if data.notes:
        trade.notes = data.notes

    db.add(trade)
    await db.flush()

    # Get symbol for response
    from app.models.asset import Asset
    asset_result = await db.execute(
        select(Asset).where(Asset.id == trade.asset_id)
    )
    asset = asset_result.scalar_one_or_none()
    symbol = asset.symbol if asset else str(trade.asset_id)

    return _build_trade_response(trade, symbol)


async def get_trades(
    user: User,
    db: AsyncSession,
    open_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[TradeResponse]:
    """Returns trade history. If open_only=True, returns only open positions."""
    from app.models.asset import Asset

    query = (
        select(Trade, Asset)
        .join(Asset, Trade.asset_id == Asset.id)
        .where(Trade.user_id == user.id)
        .order_by(Trade.entry_date.desc())
        .limit(limit)
        .offset(offset)
    )

    if open_only:
        query = query.where(Trade.exit_price.is_(None))

    result = await db.execute(query)
    rows = result.all()

    # Fetch current prices for open trades in parallel
    async def build_response(trade: Trade, asset) -> TradeResponse:
        is_open = trade.exit_price is None
        current_price = None

        if is_open:
            current_price = await _fetch_current_price(asset.asset_type, asset.symbol)

        return _build_trade_response(trade, asset.symbol, current_price)

    responses = await asyncio.gather(*[
        build_response(trade, asset)
        for trade, asset in rows
    ])

    return list(responses)


async def delete_trade(
    trade_id: int,
    user: User,
    db: AsyncSession,
) -> None:
    """Deletes a trade. Only open trades can be deleted."""

    result = await db.execute(
        select(Trade).where(
            Trade.id == trade_id,
            Trade.user_id == user.id,
        )
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.exit_price is not None:
        raise HTTPException(
            status_code=400,
            detail="Closed trades cannot be deleted — they are part of your trading history"
        )

    await db.delete(trade)
    await db.flush()


# ------------------------------------------------------------------
# Private helper
# ------------------------------------------------------------------

async def _get_asset_by_id(asset_id: int, db: AsyncSession):
    from app.models.asset import Asset
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    return result.scalar_one_or_none()