from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.holdings import Holdings
from app.models.asset import Asset
from app.providers.twelvedata_provider import twelvedata_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.portfolio import PortfolioResponse, HoldingItem


async def get_portfolio(user_id: int, db: AsyncSession) -> PortfolioResponse:

    # First, get all user holdings with their assets
    result = await db.execute(
        select(Holdings, Asset)
        .join(Asset, Holdings.asset_id == Asset.id)
        .where(Holdings.user_id == user_id)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No holdings found for user {user_id}")

    # Second, fetch the current price for each holding in parallel
    import asyncio

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
                allocation_pct=0.0,  # Calculate later when we have total portfolio value
            )
        except Exception:
            return None

    # Execute all calls to providers in parallel
    holding_items = await asyncio.gather(*[
        fetch_holding_price(holding, asset)
        for holding, asset in rows
    ])

    # Filter None (Holdings failed)
    holding_items = [h for h in holding_items if h is not None]

    # Third, calculate totals and allocation_pct
    total_value = sum(h.current_value for h in holding_items)
    total_invested = sum(h.total_invested for h in holding_items)
    total_pnl = total_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0.0

    # Assign allocation_pct now that we have the total
    for item in holding_items:
        item.allocation_pct = round(
            (item.current_value / total_value * 100) if total_value else 0.0, 2
        )

    return PortfolioResponse(
        user_id=user_id,
        total_value=round(total_value, 4),
        total_invested=round(total_invested, 4),
        total_pnl=round(total_pnl, 4),
        total_pnl_pct=round(total_pnl_pct, 4),
        holdings=holding_items,
        last_updated=datetime.utcnow(),
    )