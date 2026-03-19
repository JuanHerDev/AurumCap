from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.watchlist import Watchlist
from app.models.asset import Asset
from app.models.user import User
from app.providers.twelvedata_provider import twelvedata_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.watchlist import WatchlistResponse, WatchlistItem
from app.services.asset_service import get_or_create_asset
import asyncio

async def get_watchlist(user: User, db: AsyncSession) -> WatchlistResponse:
    # Returns the user's watchlist with live prices

    result = await db.execute(
        select(Watchlist, Asset)
        .join(Asset, Watchlist.asset_id == Asset.id)
        .where(Watchlist.user_id == user.id)
    )
    rows = result.all()

    if not rows:
        return WatchlistResponse(user_id=user.id, items=[], total=0)

    # Fetch live prices for all watchlist items in parallel
    async def fetch_price(watchlist: Watchlist, asset: Asset) -> WatchlistItem:
        try:
            if asset.asset_type == "crypto":
                data = await coinmarketcap_provider.get_price(asset.symbol)
                current_price = data.price if data else None
                change_pct = data.change_pct_24h if data else None
            else:
                data = await twelvedata_provider.get_price(asset.symbol)
                current_price = data.price if data else None
                change_pct = data.change_pct if data else None

            return WatchlistItem(
                asset_id=asset.id,
                symbol=asset.symbol,
                name=asset.name,
                asset_type=asset.asset_type,
                current_price=current_price,
                change_pct=change_pct,
            )
        except Exception:
            return WatchlistItem(
                asset_id=asset.id,
                symbol=asset.symbol,
                name=asset.name,
                asset_type=asset.asset_type,
                current_price=None,
                change_pct=None,
            )

    items = await asyncio.gather(*[
        fetch_price(watchlist, asset)
        for watchlist, asset in rows
    ])

    return WatchlistResponse(
        user_id=user.id,
        items=list(items),
        total=len(items),
    )

async def add_to_watchlist(
    symbol: str,
    user: User,
    db: AsyncSession,
) -> WatchlistItem:
    """Adds an asset to the watchlist. Creates the asset in DB if it doesn't exist."""

    # Get or create the asset
    asset = await get_or_create_asset(symbol.upper(), db)

    if not asset:
        raise HTTPException(
            status_code=404,
            detail=f"Asset '{symbol}' not found"
        )

    # Check if already in watchlist
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == user.id,
            Watchlist.asset_id == asset.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"'{symbol}' is already in your watchlist"
        )

    # Add to watchlist
    watchlist_item = Watchlist(user_id=user.id, asset_id=asset.id)
    db.add(watchlist_item)
    await db.flush()

    # Return with live price
    try:
        if asset.asset_type == "crypto":
            data = await coinmarketcap_provider.get_price(asset.symbol)
            current_price = data.price if data else None
            change_pct = data.change_pct_24h if data else None
        else:
            data = await twelvedata_provider.get_price(asset.symbol)
            current_price = data.price if data else None
            change_pct = data.change_pct if data else None
    except Exception:
        current_price = None
        change_pct = None

    return WatchlistItem(
        asset_id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        asset_type=asset.asset_type,
        current_price=current_price,
        change_pct=change_pct,
    )


async def remove_from_watchlist(
    symbol: str,
    user: User,
    db: AsyncSession,
) -> None:
    """Removes an asset from the watchlist by symbol."""

    # Find the asset
    result = await db.execute(
        select(Asset).where(Asset.symbol == symbol.upper())
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{symbol}' not found")

    # Find the watchlist entry
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == user.id,
            Watchlist.asset_id == asset.id,
        )
    )
    watchlist_item = result.scalar_one_or_none()

    if not watchlist_item:
        raise HTTPException(
            status_code=404,
            detail=f"'{symbol}' is not in your watchlist"
        )

    await db.delete(watchlist_item)
    await db.flush()
