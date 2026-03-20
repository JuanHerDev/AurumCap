from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import asyncio

from app.models.asset import Asset
from app.providers.finnhub_provider import finnhub_provider
from app.schemas.fundamentals import FundamentalsResponse
from app.core.cache import cache_get, cache_set, key_fundamentals, TTL_FUNDAMENTALS


async def get_fundamentals(symbol: str, db: AsyncSession) -> FundamentalsResponse:
    symbol = symbol.upper()

    # 1. Check cache — fundamentals change at most once per day
    cached = await cache_get(key_fundamentals(symbol))
    if cached:
        return FundamentalsResponse(**cached)

    # 2. Verify asset exists in DB and is not crypto
    # Finnhub does not provide fundamental data for crypto assets
    result = await db.execute(select(Asset).where(Asset.symbol == symbol))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{symbol}' not found")

    if asset.asset_type == "crypto":
        raise HTTPException(
            status_code=400,
            detail="Fundamentals are not available for crypto assets"
        )

    # 3. Fetch profile and metrics in parallel — two Finnhub calls
    profile, fundamentals = await asyncio.gather(
        finnhub_provider.get_profile(symbol),
        finnhub_provider.get_fundamentals(symbol),
    )

    if not fundamentals:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch fundamentals for '{symbol}'"
        )

    # 4. Build response — profile may be None for lesser-known tickers
    response = FundamentalsResponse(
        symbol=symbol,
        # Valuation
        pe_ratio=fundamentals.pe_ratio,
        pb_ratio=fundamentals.pb_ratio,
        ps_ratio=fundamentals.ps_ratio,
        ev_ebitda=fundamentals.ev_ebitda,
        # Profitability
        roe=fundamentals.roe,
        roa=fundamentals.roa,
        net_margin=fundamentals.net_margin,
        gross_margin=fundamentals.gross_margin,
        # Growth
        revenue_growth_yoy=fundamentals.revenue_growth_yoy,
        eps_growth_yoy=fundamentals.eps_growth_yoy,
        # Dividends
        dividend_yield=fundamentals.dividend_yield,
        dividend_per_share=fundamentals.dividend_per_share,
        # Balance sheet
        debt_to_equity=fundamentals.debt_to_equity,
        current_ratio=fundamentals.current_ratio,
        # Price metrics
        week_52_high=fundamentals.week_52_high,
        week_52_low=fundamentals.week_52_low,
        beta=fundamentals.beta,
    )

    # 5. Store in cache for TTL_FUNDAMENTALS seconds (24h)
    await cache_set(key_fundamentals(symbol), response.model_dump(), TTL_FUNDAMENTALS)

    return response