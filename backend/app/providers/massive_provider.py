import asyncio
from dataclasses import dataclass
from typing import Optional
from massive import RESTClient
from app.core.settings import settings

# Response Data Classes
# Internal provider contracts. Services consume these types,

@dataclass
class StockPrice:
    symbol: str
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float # Absolute difference vs. previous closing
    change_pct: float # Porcentage of change
    market_status: str # "open" | "extended-hours" | "closed" | "unknown"

@dataclass
class AssetMetadata:
    symbol: str
    name: str
    asset_type: str # "stock" | "etf"
    exchange: str
    sector: Optional[str]
    industry: Optional[str]
    description: Optional[str]
    market_cap: Optional[float]

@dataclass
class SearchResult:
    symbol: str
    name: str
    asset_type: str
    exchange: str

# Provider

class MassiveProvider:
    """Async wrapper over Massive's synchronous RESTClient
    Each public method runs the SDK in a thread pool to avoid blocking
    the FastAPI event loop."""

    def __init__(self):
        # The RESTClient is instantiated only once.
        self._client = RESTClient(api_key=settings.MASSIVE_API_KEY)

    def _get_snapshot_sync(self, symbol: str) -> Optional[StockPrice]:
        try:
                # prev day aggs — disponible en plan gratuito
            aggs = list(self._client.list_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_="2025-01-01",
                to="2099-12-31",
                limit=1,
                sort="desc",
            ))

            if not aggs:
                return None

            bar = aggs[0]

            open_  = getattr(bar, "open", 0) or 0
            high   = getattr(bar, "high", 0) or 0
            low    = getattr(bar, "low", 0) or 0
            close  = getattr(bar, "close", 0) or 0
            volume = int(getattr(bar, "volume", 0) or 0)
            vwap   = getattr(bar, "vwap", close) or close

            # Calcular cambio usando vwap como precio de apertura estimado
            prev_close = open_
            change = close - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0.0

            market_status = self._get_market_status_sync()

            return StockPrice(
                symbol=symbol.upper(),
                price=round(close, 4),
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
            print(f"[MassiveProvider] Error in {symbol}: {type(e).__name__}: {e}")
            return None
        
    def _get_metadata_sync(self, symbol: str) -> Optional[AssetMetadata]:
        """ Synchronous version — runs in thread pool. """

        try:
            details = self._client.get_ticker_details(symbol)

            if details is None:
                return None
            
            ticker_type = getattr(details, "type", "CS")
            asset_type = "etf" if ticker_type == "ETF" else "stock"

            return AssetMetadata(
                symbol=getattr(details, "ticker", symbol).upper(),
                name=getattr(details, "name", ""),
                asset_type=asset_type,
                exchange=getattr(details, "primary_exchange", ""),
                sector=getattr(details, "sic_description", None),
                industry=None,  # Massive does not directly expose industry
                description=getattr(details, "description", None),
                market_cap=getattr(details, "market_cap", None),
            )
        
        except Exception:
            return None
        
    def _search_sync(self, query: str, limit: int) -> list[SearchResult]:
        """ Synchronous version — runs in thread pool. """

        try:
            results = self._client.list_tickers(
                search=query,
                active=True,
                market="stocks",
                limit=limit,
            )

            output = []
            for item in results:
                ticker_type = getattr(item, "type", "CS")
                output.append(SearchResult(
                    symbol=getattr(item, "ticker", ""),
                    name=getattr(item, "name", ""),
                    asset_type="etf" if ticker_type == "ETF" else "stock",
                    exchange=getattr(item, "primary_exchange", ""),
                ))
                if len(output) >= limit:
                    break

            return output
        
        except Exception:
            return []
        
    def _get_market_status_sync(self) -> str:
        """ Synchronous version — runs in thread pool. """

        try:
            status = self._client.get_market_status()
            market = getattr(status, "market", "closed")

            if market == "open":
                return "open"
            elif market == "extended-hours":
                return "extended-hours"
            else:
                return "closed"
            
        except Exception:
            return "unknown"
        
    """
    Public async methods (wrap synchronous versions)
    asyncio.to_thread runs the function in Python's default thread pool
    releasing the FastAPI event loop while it waits.
    """

    async def get_price(self, symbol: str) -> Optional[StockPrice]:
        """ Current price + daily metrics for a stock or ETF """
        return await asyncio.to_thread(self._get_snapshot_sync, symbol.upper())

    async def get_asset_metadata(self, symbol: str) -> Optional[AssetMetadata]:
        """ Asset metadata: name, exchange, sector, market cap """
        return await asyncio.to_thread(self._get_metadata_sync, symbol.upper())
    
    async def search_assets(self, query: str, limit: int = 10) -> list[SearchResult]:
        """ Search for assets by symbol or name (autocomplete) """
        return await asyncio.to_thread(self._search_sync, query, limit)
    
    async def get_market_status(self) -> str:
        """ Current market status: open | extended-hours | closed | unknown """
        return await asyncio.to_thread(self._get_market_status_sync)
    
# Global instance
massive_provider = MassiveProvider()