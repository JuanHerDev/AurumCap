import asyncio
from dataclasses import dataclass
from typing import Optional
from twelvedata import TDClient
from app.core.settings import settings

@dataclass
class StockPrice:
    symbol: str
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float
    change_pct: float
    market_status: str


class TwelveDataProvider:

    def __init__(self):
        self._client = TDClient(apikey=settings.TWELVEDATA_API_KEY)

    def _get_price_sync(self, symbol: str) -> Optional[StockPrice]:

        try:
            price_data = self._client.price(symbol=symbol).as_json()

            if not price_data or "price" not in price_data:
                return None

            current_price = float(price_data["price"])

            # OHLCV + data previous day
            quote_data = self._client.quote(symbol=symbol).as_json()

            open_  = float(quote_data.get("open", current_price))
            high   = float(quote_data.get("high", current_price))
            low    = float(quote_data.get("low", current_price))
            close  = float(quote_data.get("previous_close", current_price))
            volume = int(float(quote_data.get("volume", 0)))
            change = float(quote_data.get("change", 0))
            change_pct = float(quote_data.get("percent_change", 0))
            is_market_open = quote_data.get("is_market_open", False)

            market_status = "open" if is_market_open else "closed"

            return StockPrice(
                symbol=symbol.upper(),
                price=round(current_price, 4),
                open=round(open_, 4),
                high=round(high, 4),
                low=round(low, 4),
                close=round(close, 4),
                volume=volume,
                change=round(change, 4),
                change_pct=round(change_pct, 4),
                market_status=market_status,
            )
        
        except Exception as e:
            print(f"[TwelveDataProvider] Error in {symbol}: {type(e).__name__}: {e}")
            return None
        
    async def get_price(self, symbol: str) -> Optional[StockPrice]:
        # Current price + Metrics of day in Stock or ETF
        return await asyncio.to_thread(self._get_price_sync, symbol.upper())
    
# Global instance
twelvedata_provider = TwelveDataProvider()