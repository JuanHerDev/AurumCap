import os
import requests
import asyncio
import time
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
TIMEOUT = 10  # seconds
CACHE_TTL = 60  # 1 minute cache
RATE_LIMIT_DELAY = 1.0  # 1 second between requests


@dataclass
class PriceCacheEntry:
    price: Decimal
    timestamp: float
    symbol: str
    vs_currency: str


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
        
    async def acquire(self):
        """Wait until we can make the next API call"""
        now = time.time()
        time_since_last = now - self.last_call
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
            
        self.last_call = time.time()


class CryptoPriceService:
    """
    Enhanced crypto price service with caching, rate limiting, and fallback strategies
    """
    
    def __init__(self):
        self._cache: Dict[str, PriceCacheEntry] = {}
        self._rate_limiter = RateLimiter(RATE_LIMIT_DELAY)
        self._session = None
        
    async def __aenter__(self):
        self._session = requests.Session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            self._session.close()
            
    def _get_cache_key(self, symbol: str, vs_currency: str) -> str:
        return f"{symbol.lower()}_{vs_currency.lower()}"
        
    def _get_cached_price(self, symbol: str, vs_currency: str) -> Optional[Decimal]:
        cache_key = self._get_cache_key(symbol, vs_currency)
        entry = self._cache.get(cache_key)
        
        if entry and time.time() - entry.timestamp < CACHE_TTL:
            logger.debug(f"Cache hit for {symbol}/{vs_currency}")
            return entry.price
            
        logger.debug(f"Cache miss for {symbol}/{vs_currency}")
        return None
        
    def _set_cached_price(self, symbol: str, vs_currency: str, price: Decimal):
        cache_key = self._get_cache_key(symbol, vs_currency)
        self._cache[cache_key] = PriceCacheEntry(
            price=price,
            timestamp=time.time(),
            symbol=symbol,
            vs_currency=vs_currency
        )
        
    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        """Safely convert API response to Decimal"""
        if value is None:
            return None
            
        try:
            decimal_value = Decimal(str(value))
            return decimal_value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting to Decimal: {value} - {e}")
            return None
            
    async def _fetch_price_direct(self, symbol: str, vs_currency: str) -> Optional[Decimal]:
        """Try direct price fetch by symbol/ID"""
        try:
            params = {
                "ids": symbol.lower(),
                "vs_currencies": vs_currency.lower()
            }
            
            response = self._session.get(
                f"{COINGECKO_API}/simple/price",
                params=params,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            if symbol.lower() in data and vs_currency.lower() in data[symbol.lower()]:
                price = self._to_decimal(data[symbol.lower()][vs_currency.lower()])
                if price:
                    logger.info(f"Direct price fetch successful: {symbol} = {price} {vs_currency}")
                    return price
                    
        except requests.RequestException as e:
            logger.warning(f"Direct fetch failed for {symbol}: {e}")
            
        return None
        
    async def _search_and_fetch_price(self, symbol: str, vs_currency: str) -> Optional[Decimal]:
        """Search for symbol and then fetch price"""
        try:
            # Search for the symbol
            search_params = {"query": symbol}
            search_response = self._session.get(
                f"{COINGECKO_API}/search",
                params=search_params,
                timeout=TEOUT
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            
            coins = search_data.get("coins", [])
            if not coins:
                logger.warning(f"No coins found for symbol: {symbol}")
                return None
                
            # Find best match
            for coin in coins:
                coin_symbol = coin.get("symbol", "").lower()
                coin_id = coin.get("id", "").lower()
                
                if coin_symbol == symbol.lower() or coin_id == symbol.lower():
                    # Fetch price for found coin
                    price_params = {
                        "ids": coin_id,
                        "vs_currencies": vs_currency.lower()
                    }
                    
                    price_response = self._session.get(
                        f"{COINGECKO_API}/simple/price",
                        params=price_params,
                        timeout=TIMEOUT
                    )
                    price_response.raise_for_status()
                    price_data = price_response.json()
                    
                    if coin_id in price_data and vs_currency.lower() in price_data[coin_id]:
                        price = self._to_decimal(price_data[coin_id][vs_currency.lower()])
                        if price:
                            logger.info(f"Search price fetch successful: {symbol} -> {coin_id} = {price} {vs_currency}")
                            return price
                    break
                    
        except requests.RequestException as e:
            logger.error(f"Search and fetch failed for {symbol}: {e}")
            
        return None
        
    async def get_crypto_price(self, symbol: str, vs_currency: str = "usd") -> Optional[Decimal]:
        """
        Get crypto price with caching, rate limiting, and fallback strategies
        """
        if not symbol or not isinstance(symbol, str):
            logger.error("Invalid symbol provided")
            return None
            
        symbol = symbol.strip()
        if not symbol:
            logger.error("Empty symbol provided")
            return None
            
        # Check cache first
        cached_price = self._get_cached_price(symbol, vs_currency)
        if cached_price is not None:
            return cached_price
            
        # Apply rate limiting
        await self._rate_limiter.acquire()
        
        try:
            # Try direct fetch first
            price = await self._fetch_price_direct(symbol, vs_currency)
            
            # If direct fails, try search and fetch
            if price is None:
                price = await self._search_and_fetch_price(symbol, vs_currency)
                
            # Cache the result (even if None to avoid repeated failed requests)
            if price is not None:
                self._set_cached_price(symbol, vs_currency, price)
            else:
                logger.warning(f"Could not fetch price for {symbol}")
                # Cache None for a shorter time to avoid hammering API for invalid symbols
                self._set_cached_price(symbol, vs_currency, Decimal("0"))
                
            return price
            
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {symbol}: {e}")
            return None


# Global service instance
_crypto_service = CryptoPriceService()

async def get_crypto_price(symbol: str, vs_currency: str = "usd") -> Optional[Decimal]:
    """
    Main async function to get crypto price
    """
    async with _crypto_service as service:
        return await service.get_crypto_price(symbol, vs_currency)


# Sync wrapper for backward compatibility
def get_crypto_price_sync(symbol: str, vs_currency: str = "usd") -> Optional[Decimal]:
    """
    Synchronous wrapper for backward compatibility
    """
    try:
        return asyncio.run(get_crypto_price(symbol, vs_currency))
    except Exception as e:
        logger.error(f"Error in sync crypto price fetch: {e}")
        return None