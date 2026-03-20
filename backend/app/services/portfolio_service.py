from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import asyncio

from app.models.holdings import Holdings
from app.models.asset import Asset
from app.providers.twelvedata_provider import twelvedata_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.portfolio import PortfolioResponse, HoldingItem
from app.core.cache import (
    cache_get, cache_set, cache_delete,
    key_portfolio, TTL_PORTFOLIO,
)


async def get_portfolio(user_id: int, db: AsyncSession) -> PortfolioResponse:

    # 1. Check cache — portfolio value is cached for 60s
    cached = await cache_get(key_portfolio(user_id))
    if cached:
        return PortfolioResponse(**cached)

    # 2. Fetch all user holdings with their asset info
    result = await db.execute(
        select(Holdings, Asset)
        .join(Asset, Holdings.asset_id == Asset.id)
        .where(Holdings.user_id == user_id)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No holdings found for user {user_id}")

    # 3. Fetch live price for each holding in parallel
    async def fetch_holding_price(holding: Holdings, asset: Asset) -> HoldingItem | None:
        try:
            if asset.asset_type == "crypto":
                data = await coinmarketcap_provider.get_price(asset.symbol)
                current_price = data.price if data else holding.avg_price
            else:
                data = await twelvedata_provider.get_price(asset.symbol)
                current_price = data.price if data else holding.avg_price

            current_value = holding.quantity * current_price
            total_invested = holding.quantity * holding.avg_price
            pnl = current_value - total_invested
            pnl_pct = (pnl / total_invested * 100) if total_invested else 0.0

            return HoldingItem(
                asset_id=asset.id,
                symbol=asset.symbol,
                name=asset.name,
                asset_type=asset.asset_type,
                quantity=holding.quantity,
                avg_price=holding.avg_price,
                current_price=current_price,
                current_value=current_value,
                total_invested=total_invested,
                pnl=round(pnl, 4),
                pnl_pct=round(pnl_pct, 4),
                allocation_pct=0.0,  # Calculated below once we have total value
            )
        except Exception:
            return None

    # Run all price fetches concurrently
    holding_items = await asyncio.gather(*[
        fetch_holding_price(holding, asset)
        for holding, asset in rows
    ])

    # Filter out any failed fetches
    holding_items = [h for h in holding_items if h is not None]

    # 4. Calculate portfolio totals
    total_value = sum(h.current_value for h in holding_items)
    total_invested = sum(h.total_invested for h in holding_items)
    total_pnl = total_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0.0

    # Assign allocation percentage now that we have the total portfolio value
    for item in holding_items:
        item.allocation_pct = round(
            (item.current_value / total_value * 100) if total_value else 0.0, 2
        )

    response = PortfolioResponse(
        user_id=user_id,
        total_value=round(total_value, 4),
        total_invested=round(total_invested, 4),
        total_pnl=round(total_pnl, 4),
        total_pnl_pct=round(total_pnl_pct, 4),
        holdings=holding_items,
        last_updated=datetime.utcnow(),
    )

    # 5. Store in cache for TTL_PORTFOLIO seconds (60s)
    await cache_set(key_portfolio(user_id), response.model_dump(), TTL_PORTFOLIO)

    return response


async def invalidate_portfolio_cache(user_id: int) -> None:
    """
    Invalidates the portfolio cache for a specific user.
    Must be called after any transaction that modifies holdings
    (create, update, or delete) to ensure the next request
    reflects the latest portfolio state.
    """
    await cache_delete(key_portfolio(user_id))