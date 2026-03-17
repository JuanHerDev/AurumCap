from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.asset import Asset
from app.providers.finnhub_provider import finnhub_provider
from app.schemas.fundamentals import FundamentalsResponse


async def get_fundamentals(symbol: str, db: AsyncSession) -> FundamentalsResponse:
    symbol = symbol.upper()

    # First, verify that the asset exists in the database and is a stock or ETF
    # Finnhub lacks fundamental crypto data
    result = await db.execute(
        select(Asset).where(Asset.symbol == symbol)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{symbol}' not found")

    if asset.asset_type == "crypto":
        raise HTTPException(
            status_code=400,
            detail="Fundamentals are not available for crypto assets"
        )

    # Second, get profile and metrics in parallel — two calls to Finnhub
    import asyncio

    profile, fundamentals = await asyncio.gather(
        finnhub_provider.get_profile(symbol),
        finnhub_provider.get_fundamentals(symbol),
    )

    if not fundamentals:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch fundamentals for '{symbol}'"
        )

    # Third, combine profile data with financial metrics
    # The profile can be None for lesser-known tickets — we handle gracefully
    return FundamentalsResponse(
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
        # Balance
        debt_to_equity=fundamentals.debt_to_equity,
        current_ratio=fundamentals.current_ratio,
        # Price
        week_52_high=fundamentals.week_52_high,
        week_52_low=fundamentals.week_52_low,
        beta=fundamentals.beta,
    )