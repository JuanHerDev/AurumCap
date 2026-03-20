from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import asyncio

from app.models.watchlist import Watchlist
from app.models.asset import Asset
from app.models.user import User
from app.providers.twelvedata_provider import twelvedata_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.watchlist import WatchlistResponse, WatchlistItem
from app.services.asset_service import get_or_create_asset


async def _fetch_price_for_item(watchlist: Watchlist, asset: Asset) -> WatchlistItem:
    """Fetches live price for a single watchlist item. Rate limiter is applied
    inside the provider for TwelveData calls."""
    try:
        if asset.asset_type == "crypto":
            data = await coinmarketcap_provider.get_price(asset.symbol)
            current_price = data.price if data else None
            change_pct    = data.change_pct_24h if data else None
        else:
            # Rate limiter applied inside twelvedata_provider.get_price
            data = await twelvedata_provider.get_price(asset.symbol)
            current_price = data.price if data else None
            change_pct    = data.change_pct if data else None

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


async def get_watchlist(user: User, db: AsyncSession) -> WatchlistResponse:
    """
    Returns the user's watchlist with live prices.
    Crypto fetched in parallel (CMC has no strict per-minute limit).
    Stocks/ETFs fetched sequentially via rate limiter inside provider.
    """
    result = await db.execute(
        select(Watchlist, Asset)
        .join(Asset, Watchlist.asset_id == Asset.id)
        .where(Watchlist.user_id == user.id)
    )
    rows = result.all()

    if not rows:
        return WatchlistResponse(user_id=user.id, items=[], total=0)

    # Separate crypto and stocks for different fetch strategies
    crypto_rows = [(w, a) for w, a in rows if a.asset_type == "crypto"]
    stock_rows  = [(w, a) for w, a in rows if a.asset_type != "crypto"]

    # Crypto in parallel — CMC handles concurrent requests fine
    crypto_items = await asyncio.gather(*[
        _fetch_price_for_item(w, a) for w, a in crypto_rows
    ])

    # Stocks/ETFs sequential — rate limiter inside provider handles pacing
    stock_items = []
    for w, a in stock_rows:
        item = await _fetch_price_for_item(w, a)
        stock_items.append(item)

    # Preserve original order by sorting back to DB order
    symbol_order = {a.symbol: i for i, (_, a) in enumerate(rows)}
    all_items = sorted(
        list(crypto_items) + stock_items,
        key=lambda item: symbol_order.get(item.symbol, 999)
    )

    return WatchlistResponse(
        user_id=user.id,
        items=all_items,
        total=len(all_items),
    )


async def add_to_watchlist(
    symbol: str,
    user: User,
    db: AsyncSession,
) -> WatchlistItem:
    """
    Adds an asset to the watchlist.
    Creates the asset in DB first if it doesn't exist.
    """
    # Get or create the asset record
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

    # Persist the watchlist entry
    watchlist_item = Watchlist(user_id=user.id, asset_id=asset.id)
    db.add(watchlist_item)
    await db.flush()

    # Return with live price — rate limiter applied inside provider
    try:
        if asset.asset_type == "crypto":
            data = await coinmarketcap_provider.get_price(asset.symbol)
            current_price = data.price if data else None
            change_pct    = data.change_pct_24h if data else None
        else:
            data = await twelvedata_provider.get_price(asset.symbol)
            current_price = data.price if data else None
            change_pct    = data.change_pct if data else None
    except Exception:
        current_price = None
        change_pct    = None

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
        raise HTTPException(
            status_code=404,
            detail=f"Asset '{symbol}' not found"
        )

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