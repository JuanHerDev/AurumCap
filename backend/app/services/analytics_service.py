import asyncio
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

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
# Each range maps to a number of days and a TwelveData timespan
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
# Runs in a thread pool to avoid blocking the async event loop
# ------------------------------------------------------------------

def _get_historical_prices_sync(
    symbol: str,
    from_date: str,
    to_date: str,
    timespan: str,
) -> dict:
    """
    Synchronous function — runs in thread pool via asyncio.to_thread.
    Returns {date_str: close_price} for the given date range.

    TwelveData SDK returns a tuple of dicts (one per data point),
    not a list — this is intentional SDK behavior, not an error.
    We convert it to a list before processing.
    """
    from twelvedata import TDClient
    from app.core.settings import settings

    try:
        client = TDClient(apikey=settings.TWELVEDATA_API_KEY)

        # Map internal timespan names to TwelveData interval strings
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

        # TwelveData SDK returns different types depending on the response:
        # - tuple: successful response, each element is a {datetime, ohlcv} dict
        # - dict:  API error response (e.g. invalid symbol, rate limit)
        # - list:  alternative success format in some SDK versions
        if isinstance(result, tuple):
            # FIX: convert tuple of dicts to list for uniform processing
            data = list(result)
        elif isinstance(result, dict):
            # API returned an error object
            print(f"[Analytics] {symbol} API error: {result}")
            return {}
        elif isinstance(result, list):
            data = result
        else:
            print(f"[Analytics] {symbol} unexpected response type: {type(result)}")
            return {}

        if not data:
            return {}

        # Build {date_str: close_price} dict
        # Truncate datetime to date only (first 10 chars of "YYYY-MM-DD HH:MM:SS")
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
    """Async wrapper — runs the sync function in the default thread pool."""
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
    Returns the portfolio value over time for the given range.

    Strategy:
    1. Use existing DB snapshots where available (fast)
    2. Reconstruct from holdings + historical prices for missing dates (accurate)
    """
    if range_ not in RANGE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid range. Use: {list(RANGE_CONFIG.keys())}"
        )

    config = RANGE_CONFIG[range_]
    today = date.today()
    from_date = today - timedelta(days=config["days"])

    # 1. Fetch current holdings with their asset info
    result = await db.execute(
        select(Holdings, Asset)
        .join(Asset, Holdings.asset_id == Asset.id)
        .where(Holdings.user_id == user_id)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail="No holdings found for this user")

    # 2. Fetch existing snapshots in the date range
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

    # 3. Fetch historical prices sequentially to respect TwelveData rate limits
    # (800 req/day on free plan — parallel calls would exhaust it quickly)
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
                "prices": prices,  # {date_str: close_price}
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
        await asyncio.sleep(0.5)  # 500ms delay between calls to avoid rate limits

    # 4. Collect all available dates across all holdings
    all_dates = set()
    for hd in holdings_data:
        all_dates.update(hd["prices"].keys())

    if not all_dates:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch historical prices"
        )

    all_dates = sorted(all_dates)

    # 5. Build time series — one SnapshotPoint per date
    history_points = []

    for date_str in all_dates:
        snap_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()

        # Use existing DB snapshot if available for this date
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
                # Fall back to the closest available prior price
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

    return PortfolioHistoryResponse(
        user_id=user_id,
        range=range_,
        snapshots=history_points,
    )


# ------------------------------------------------------------------
# Asset allocation (donut chart)
# ------------------------------------------------------------------

async def get_asset_allocation(
    user_id: int,
    db: AsyncSession,
) -> AssetAllocationResponse:
    """
    Returns the current value distribution across holdings.
    Fetches live prices for all assets in parallel.
    """
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
                data = await twelvedata_provider.get_price(asset.symbol)
                price = data.price if data else holding.avg_price

            return {
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "current_value": holding.quantity * price,
            }
        except Exception:
            # Fall back to avg_price if live price fetch fails
            return {
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "current_value": holding.quantity * holding.avg_price,
            }

    # Allocation uses live prices — parallel calls are fine here
    # (only one call per asset, not a batch of historical data)
    items_data = await asyncio.gather(*[
        fetch_current_value(holding, asset)
        for holding, asset in rows
    ])

    total_value = sum(item["current_value"] for item in items_data)

    # Sort by value descending so the donut chart renders largest slice first
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

    return AssetAllocationResponse(
        user_id=user_id,
        total_value=round(total_value, 2),
        allocations=allocations,
    )


# ------------------------------------------------------------------
# Portfolio vs benchmark (SPY)
# ------------------------------------------------------------------

async def get_benchmark_comparison(
    user_id: int,
    range_: str,
    db: AsyncSession,
) -> dict:
    """
    Compares portfolio performance against SPY (S&P 500 ETF).
    Both series are normalized to base 100 for visual comparison.

    Example: if portfolio started at $30,000 and is now $47,000,
    it shows as 100 → 156.6. If SPY went from $580 to $600,
    it shows as 100 → 103.4. Makes performance comparison intuitive.
    """
    if range_ not in RANGE_CONFIG:
        raise HTTPException(status_code=400, detail="Invalid range.")

    config = RANGE_CONFIG[range_]
    today = date.today()
    from_date = today - timedelta(days=config["days"])

    # Fetch portfolio history and SPY prices concurrently
    # SPY fetch runs in parallel because it's independent of the user's holdings
    portfolio_history, spy_prices = await asyncio.gather(
        get_portfolio_history(user_id, range_, db),
        _get_historical_prices(
            symbol="SPY",
            asset_type="stock",
            from_date=from_date.strftime("%Y-%m-%d"),
            to_date=today.strftime("%Y-%m-%d"),
            timespan=config["timespan"],
        ),
    )

    if not portfolio_history.snapshots or not spy_prices:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch benchmark data"
        )

    # Normalize both series to base 100 at the start of the period
    first_portfolio = portfolio_history.snapshots[0].total_value
    spy_dates = sorted(spy_prices.keys())
    first_spy = spy_prices[spy_dates[0]] if spy_dates else 1

    portfolio_normalized = [
        {
            "date": p.date.isoformat(),
            "value": round(p.total_value / first_portfolio * 100, 2),
        }
        for p in portfolio_history.snapshots
    ]

    spy_normalized = [
        {
            "date": date_str,
            "value": round(spy_prices[date_str] / first_spy * 100, 2),
        }
        for date_str in spy_dates
    ]

    # Calculate total return for the period
    portfolio_return = round(
        (portfolio_history.snapshots[-1].total_value / first_portfolio - 1) * 100, 2
    ) if len(portfolio_history.snapshots) > 1 else 0.0

    spy_return = round(
        (spy_prices[spy_dates[-1]] / first_spy - 1) * 100, 2
    ) if len(spy_dates) > 1 else 0.0

    return {
        "user_id": user_id,
        "range": range_,
        "portfolio": portfolio_normalized,
        "benchmark": spy_normalized,
        "benchmark_symbol": "SPY",
        "portfolio_return_pct": portfolio_return,
        "benchmark_return_pct": spy_return,
        "outperforming": portfolio_return > spy_return,
    }