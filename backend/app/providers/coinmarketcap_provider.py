import httpx
from dataclasses import dataclass
from typing import Optional
from app.core.settings import settings

# Dataclasses response

@dataclass
class CryptoPrice:
    symbol: str
    name: str
    price: float
    change_24h: float        # Absolute difference
    change_pct_24h: float    # Percentage change 24h
    change_pct_7d: float     # Percentage change 7dh
    volume_24h: float
    market_cap: float
    rank: int

@dataclass
class CryptoMetadata:
    symbol: str
    name: str
    slug: str
    description: Optional[str]
    logo: Optional[str]
    website: Optional[str]
    cmc_id: int

@dataclass
class CryptoSearchResult:
    symbol: str
    name: str
    slug: str
    rank: int
    cmc_id: int

# Provider

class CoinMarketCapProvider:
    BASE_URL = "https://pro-api.coinmarketcap.com"

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:

        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "X-CMC_PRO_API_KEY": settings.COINMARKETCAP_API_KEY,
                    "Accept": "application/json",
                },
                timeout=10.0,
            )
        return self._client
    
    async def close(self):

        if self._client and not self._client.is_closed:
            await self._client.aclose()

    """
    Current price of one or more cryptocurrencies per symbol
    Endpoint: GET /v2/cryptocurrency/quotes/latest
    """

    async def get_price(self, symbol: str) -> Optional[CryptoPrice]:

        client = await self._get_client()
        symbol = symbol.upper()

        try:
            resp = await client.get(
                "/v2/cryptocurrency/quotes/latest",
                params={"symbol": symbol, "convert": "USD"},
            )
            resp.raise_for_status()
            data = resp.json()

            # CMC returns a list per symbol (there may be duplicates)
            entries = data.get("data", {}).get(symbol)

            if not entries:
                return None
            
            # Take the one with the highest market cap if there are duplicates
            entry = max(entries, key=lambda x: x.get("quote", {}).get("USD", {}).get("market_cap") or 0)
            quote = entry.get("quote", {}).get("USD", {})

            price = quote.get("price", 0)
            change_pct_24h = quote.get("percent_change_24h", 0) or 0
            change_24h = price * change_pct_24h / 100 if price else 0

            return CryptoPrice(
                symbol=symbol,
                name=entry.get("name", ""),
                price=round(price, 6),
                change_24h=round(change_24h, 6),
                change_pct_24h=round(change_pct_24h, 4),
                change_pct_7d=round(quote.get("percent_change_7d", 0) or 0, 4),
                volume_24h=quote.get("volume_24h", 0) or 0,
                market_cap=quote.get("market_cap", 0) or 0,
                rank=entry.get("cmc_rank", 0) or 0,
            )
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                return None # Symbol not found
            raise
        except httpx.RequestError:
            raise

    """
    Cryptocurrency metadata (description, logo, website)
    Endpoint: GET /v2/cryptocurrency/info
    """

    async def get_metadata(self, symbol: str) -> Optional[CryptoMetadata]:

        client = await self._get_client()
        symbol = symbol.upper()

        try:
            resp = await client.get(
                "/v2/cryptocurrency/info",
                params={"symbol": symbol},
            )
            resp.raise_for_status()
            data = resp.json()

            entries = data.get("data", {}).get(symbol)
            if not entries:
                return None
            
            entry = entries[0] if isinstance(entries, list) else entries
            urls = entry.get("urls", {})
            websites = urls.get("website", [])

            return CryptoMetadata(
                symbol=symbol,
                name=entry.get("name", ""),
                slug=entry.get("slug", ""),
                description=entry.get("description"),
                logo=entry.get("logo"),
                website=websites[0] if websites else None,
                cmc_id=entry.get("id", 0),
            )
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                return None
            raise

    """
    Cryptocurrency search (top by rank, filtered by query)
    CMC doesn't have a search endpoint — we use listings and filter locally
    Endpoint: GET /v1/cryptocurrency/map
    """

    async def search_assets(self, query: str, limit: int = 10) -> list[CryptoSearchResult]:

        client = await self._get_client()
        query_lower = query.lower()

        try:
            resp = await client.get(
                "/v1/cryptocurrency/map",
                params={
                    "listing_status": "active",
                    "limit": 5000,
                    "sort": "cmc_rank",
                },
            )
            resp.raise_for_status()
            entries = resp.json().get("data", [])

            results = []
            for entry in entries:
                name = (entry.get("name") or "").lower()
                symbol = (entry.get("symbol") or "").lower()

                if query_lower in symbol or query_lower in name:
                    results.append(CryptoSearchResult(
                        symbol=entry.get("symbol", ""),
                        name=entry.get("name", ""),
                        slug=entry.get("slug", ""),
                        rank=entry.get("rank") or 0,
                        cmc_id=entry.get("id", 0),
                    ))

                if len(results) >= limit:
                    break

            return results
        
        except httpx.HTTPStatusError:
            return []
        
    """
    Top N cryptos by market cap
    #Endpoint: GET /v1/cryptocurrency/listings/latest
    """

    async def get_top_cryptos(self, limit: int = 20) -> list[CryptoPrice]:

        client = await self._get_client()

        try:
            resp = await client.get(
                "/v1/cryptocurrency/listings/latest",
                params={
                    "limit": limit,
                    "convert": "USD",
                    "sort": "market_cap",
                },
            )
            resp.raise_for_status()
            entries = resp.json().get("data", [])

            results = []

            for entry in entries:
                quote = entry.get("quote", {}).get("USD", {})
                price = quote.get("price", 0)
                change_pct_24h = quote.get("percent_change_24h", 0) or 0

                results.append(CryptoPrice(
                    symbol=entry.get("symbol", ""),
                    name=entry.get("name", ""),
                    price=round(price, 6),
                    change_24h=round(price * change_pct_24h / 100, 6) if price else 0,
                    change_pct_24h=round(change_pct_24h, 4),
                    change_pct_7d=round(quote.get("percent_change_7d", 0) or 0, 4),
                    volume_24h=quote.get("volume_24h", 0) or 0,
                    market_cap=quote.get("market_cap", 0) or 0,
                    rank=entry.get("cmc_rank", 0) or 0,
                ))

            return results
        
        except httpx.HTTPStatusError:
            return []
        
# Global instance
coinmarketcap_provider = CoinMarketCapProvider()