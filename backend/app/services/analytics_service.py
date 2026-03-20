import asyncio
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.rate_limiter import twelvedata_limiter
from app.core.cache import (
    cache_get, cache_set,
    key_history, key_allocation,
    TTL_HISTORY, TTL_ALLOCATION,
)
from app.models.holdings import Holdings
from app.models.asset import Asset
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.providers.twelvedata_provider import twelvedata_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.analytics import (
    PortfolioHistoryResponse,
    SnapshotPoint,
    AssetAllocationResponse,
    AssetAllocationItem,
)


# ------------------------------------------------------------------
# Range configuration
# ------------------------------------------------------------------

RANGE_CONFIG = {
    "1D":  {"days": 1,    "timespan": "minute"},
    "1W":  {"days": 7,    "timespan": "day"},
    "1M":  {"days": 30,   "timespan": "day"},
    "3M":  {"days": 90,   "timespan": "day"},
    "1Y":  {"days": 365,  "timespan": "week"},
    "ALL": {"days": 1825, "timespan": "week"},
}


# ------------------------------------------------------------------
# Private helper — fetch historical prices from TwelveData
# Rate limiter acquired before each call to prevent 429 errors
# ------------------------------------------------------------------

def _get_historical_prices_sync(
    symbol: str,
    from_date: str,
    to_date: str,
    timespan: str,
) -> dict:
    """
    Synchronous — runs in thread pool via asyncio.to_thread.
    Returns {date_str: close_price} for the given date range.

    TwelveData SDK returns a tuple of dicts (one per data point),
    not a list — intentional SDK behavior. We convert it to a list.
    """
    from twelvedata import TDClient
    from app.core.settings import settings

    try:
        client = TDClient(apikey=settings.TWELVEDATA_API_KEY)

        interval_map = {
            "minute": "30min",
            "day":    "1day",
            "week":   "1week",
        }
        interval = interval_map.get(timespan, "1day")

        result = client.time_series(
            symbol=symbol,
            interval=interval,
            start_date=from_date,
            end_date=to_date,
            outputsize=500,
        ).as_json()

        if isinstance(result, tuple):
            data = list(result)
        elif isinstance(result, dict):
            print(f"[Analytics] {symbol} API error: {result}")
            return {}
        elif isinstance(result, list):
            data = result
        else:
            print(f"[Analytics] {symbol} unexpected type: {type(result)}")
            return {}

        if not data:
            return {}

        return {
            entry["datetime"][:10]: float(entry["close"])
            for entry in data
            if "datetime" in entry and "close" in entry
        }

    except Exception as e:
        print(f"[Analytics] Error fetching {symbol}: {type(e).__name__}: {e}")
        return {}


async def _get_historical_prices(
    symbol: str,
    asset_type: str,
    from_date: str,
    to_date: str,
    timespan: str,
) -> dict:
    """
    Async wrapper with rate limiting.
    Acquires a limiter slot before each call to stay under
    TwelveData's 8 credits/min free plan limit.
    """
    await twelvedata_limiter.acquire()
    return await asyncio.to_thread(
        _get_historical_prices_sync,
        symbol, from_date, to_date, timespan,
    )


# ------------------------------------------------------------------
# Portfolio historical value (line chart)
# ------------------------------------------------------------------

async def get_portfolio_history(
    user_id: int,
    range_: str,
    db: AsyncSession,
) -> PortfolioHistoryResponse:
    """
    Returns portfolio value over time for the given range.
    Results are cached for 1 hour — historical prices don't change,
    so there's no reason to re-fetch them on every page visit.

    Strategy:
    1. Return from cache if available (instant)
    2. Use DB snapshots where available (fast)
    3. Reconstruct from holdings + TwelveData prices (slow, rate-limited)
    """
    if range_ not in RANGE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid range. Use: {list(RANGE_CONFIG.keys())}"
        )

    # 1. Check cache first — historical data changes at most once per day
    cached = await cache_get(key_history(user_id, range_))
    if cached:
        print(f"[Analytics] Cache hit — history {user_id}/{range_}")
        return PortfolioHistoryResponse(**cached)

    config = RANGE_CONFIG[range_]
    today = date.today()
    from_date = today - timedelta(days=config["days"])

    # 2. Fetch holdings
    result = await db.execute(
        select(Holdings, Asset)
        .join(Asset, Holdings.asset_id == Asset.id)
        .where(Holdings.user_id == user_id)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail="No holdings found for this user")

    # 3. Fetch existing DB snapshots in range
    snap_result = await db.execute(
        select(PortfolioSnapshot)
        .where(
            PortfolioSnapshot.user_id == user_id,
            PortfolioSnapshot.date >= datetime.combine(
                from_date, datetime.min.time()
            ),
        )
        .order_by(PortfolioSnapshot.date.asc())
    )
    existing_snapshots = snap_result.scalars().all()
    snapshot_dates = {s.date.date() for s in existing_snapshots}

    # 4. Fetch historical prices sequentially — rate limiter handles pacing
    async def fetch_historical_prices(holding: Holdings, asset: Asset) -> dict:
        try:
            prices = await _get_historical_prices(
                symbol=asset.symbol,
                asset_type=asset.asset_type,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=today.strftime("%Y-%m-%d"),
                timespan=config["timespan"],
            )
            return {
                "asset_id": asset.id,
                "symbol": asset.symbol,
                "quantity": holding.quantity,
                "avg_price": holding.avg_price,
                "prices": prices,
            }
        except Exception as e:
            print(f"[Analytics] fetch error {asset.symbol}: {e}")
            return {
                "asset_id": asset.id,
                "symbol": asset.symbol,
                "quantity": holding.quantity,
                "avg_price": holding.avg_price,
                "prices": {},
            }

    holdings_data = []
    for holding, asset in rows:
        data = await fetch_historical_prices(holding, asset)
        holdings_data.append(data)

    # 5. Collect all available dates
    all_dates = set()
    for hd in holdings_data:
        all_dates.update(hd["prices"].keys())

    if not all_dates:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch historical prices"
        )

    all_dates = sorted(all_dates)

    # 6. Build time series — one SnapshotPoint per date
    history_points = []

    for date_str in all_dates:
        snap_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()

        # Use DB snapshot if available for this date
        if snap_date in snapshot_dates:
            snap = next(
                s for s in existing_snapshots
                if s.date.date() == snap_date
            )
            history_points.append(SnapshotPoint(
                date=snap.date,
                total_value=snap.total_value,
                total_invested=snap.total_invested,
                pnl=snap.pnl,
                pnl_pct=(snap.pnl / snap.total_invested * 100)
                    if snap.total_invested else 0.0,
            ))
            continue

        # Reconstruct from historical prices
        total_value = 0.0
        total_invested = 0.0
        valid = True

        for hd in holdings_data:
            price = hd["prices"].get(date_str)

            if price is None:
                available = [d for d in hd["prices"].keys() if d <= date_str]
                price = hd["prices"][available[-1]] if available else None

            if price is None:
                valid = False
                break

            total_value += hd["quantity"] * price
            total_invested += hd["quantity"] * hd["avg_price"]

        if not valid:
            continue

        pnl = total_value - total_invested
        pnl_pct = (pnl / total_invested * 100) if total_invested else 0.0

        history_points.append(SnapshotPoint(
            date=datetime.strptime(date_str[:10], "%Y-%m-%d"),
            total_value=round(total_value, 2),
            total_invested=round(total_invested, 2),
            pnl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 4),
        ))

    response = PortfolioHistoryResponse(
        user_id=user_id,
        range=range_,
        snapshots=history_points,
    )

    # 7. Cache for 1 hour — historical prices don't change
    await cache_set(key_history(user_id, range_), response.model_dump(), TTL_HISTORY)
    print(f"[Analytics] Cached history {user_id}/{range_} for {TTL_HISTORY}s")

    return response


# ------------------------------------------------------------------
# Asset allocation (donut chart)
# ------------------------------------------------------------------

async def get_asset_allocation(
    user_id: int,
    db: AsyncSession,
) -> AssetAllocationResponse:
    """
    Returns current value distribution across holdings.
    Cached for 5 minutes — uses live prices but doesn't need
    to be updated on every single page visit.
    """
    # Check cache first
    cached = await cache_get(key_allocation(user_id))
    if cached:
        print(f"[Analytics] Cache hit — allocation {user_id}")
        return AssetAllocationResponse(**cached)

    result = await db.execute(
        select(Holdings, Asset)
        .join(Asset, Holdings.asset_id == Asset.id)
        .where(Holdings.user_id == user_id)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail="No holdings found for this user")

    async def fetch_current_value(holding: Holdings, asset: Asset) -> dict:
        try:
            if asset.asset_type == "crypto":
                data = await coinmarketcap_provider.get_price(asset.symbol)
                price = data.price if data else holding.avg_price
            else:
                # Rate limiter applied inside twelvedata_provider.get_price
                data = await twelvedata_provider.get_price(asset.symbol)
                price = data.price if data else holding.avg_price

            return {
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "current_value": holding.quantity * price,
            }
        except Exception:
            return {
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "current_value": holding.quantity * holding.avg_price,
            }

    # Sequential to respect rate limiter
    items_data = []
    for holding, asset in rows:
        item = await fetch_current_value(holding, asset)
        items_data.append(item)

    total_value = sum(item["current_value"] for item in items_data)

    allocations = [
        AssetAllocationItem(
            symbol=item["symbol"],
            name=item["name"],
            asset_type=item["asset_type"],
            current_value=round(item["current_value"], 2),
            allocation_pct=round(
                item["current_value"] / total_value * 100, 2
            ) if total_value else 0.0,
        )
        for item in sorted(
            items_data,
            key=lambda x: x["current_value"],
            reverse=True,
        )
    ]

    response = AssetAllocationResponse(
        user_id=user_id,
        total_value=round(total_value, 2),
        allocations=allocations,
    )

    # Cache for 5 minutes
    await cache_set(key_allocation(user_id), response.model_dump(), TTL_ALLOCATION)

    return response
