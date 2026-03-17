from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.providers.twelvedata_provider import twelvedata_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.price import PriceResponse
from app.services.asset_service import get_or_create_asset


async def get_price(symbol: str, db: AsyncSession) -> PriceResponse:
    symbol = symbol.upper()

    asset = await get_or_create_asset(symbol, db)

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{symbol}' not found")

    if asset.asset_type == "crypto":
        data = await coinmarketcap_provider.get_price(symbol)

        if not data:
            raise HTTPException(status_code=502, detail=f"Could not fetch price for '{symbol}'")

        return PriceResponse(
            symbol=data.symbol,
            price=data.price,
            open=0.0,
            high=0.0,
            low=0.0,
            close=0.0,
            volume=int(data.volume_24h),
            change=data.change_24h,
            change_pct=data.change_pct_24h,
            market_status="open",
            change_pct_7d=data.change_pct_7d,
            volume_24h=data.volume_24h,
            market_cap=data.market_cap,
            rank=data.rank,
        )

    else:
        # stock or ETF → Twelve Data
        data = await twelvedata_provider.get_price(symbol)

        if not data:
            raise HTTPException(status_code=502, detail=f"Could not fetch price for '{symbol}'")

        return PriceResponse(
            symbol=data.symbol,
            price=data.price,
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume,
            change=data.change,
            change_pct=data.change_pct,
            market_status=data.market_status,
        )