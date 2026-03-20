import json
from typing import Any, Callable
from functools import wraps
from redis.asyncio import Redis
from app.core.redis import get_redis


# TTL constants (seconds)

TTL_PRICE = 30              # 30s  - prices change frequently
TTL_MARKET_STATUS = 60      # 1m - market status changes rarely
TTL_SEARCH = 300            # 5m - search results are stable
TTL_FUNDAMENTALS = 86400    # 24h - fundamentals change daily at most
TTL_PORTFOLIO = 60          # 1m - portfolio value with live prices


# Low-level cache operations

async def cache_get(key: str) -> Any | None:
    """Returns cache value or None if not found or expired"""
    try:
        redis = get_redis()
        value = await redis.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as e:
        print(f"[Cache] Get error for '{key}': {e}")
        return None

async def cache_set(key: str, value: Any, ttl: int) -> None:
    """Stores a value in cache with a TTL in seconds"""
    try:
        redis = get_redis()
        await redis.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        print(f"[Cache] Set error for '{key}': {e}")

async def cache_delete(key: str) -> None:
    """Deletes a specific cache key."""
    try:
        redis = get_redis()
        await redis.delete(key)
    except Exception as e:
        print(f"[Cache] DELETE error for '{key}': {e}")

async def cache_delete_pattern(pattern: str) -> None:
    """Deletes all keys matching a pattern. Use with caution in production."""
    try:
        redis = get_redis()
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        print(f"[Cache] DELETE pattern error for '{pattern}': {e}")

# Cache key builders - centralized to avoid key typos

def key_price(symbol: str) -> str:
    return f"price:{symbol.upper()}"

def key_market_status() -> str:
    return "market:status"

def key_search(query: str, limit: int) -> str:
    return f"search:{query.lower()}:{limit}"

def key_fundamentals(symbol: str) -> str:
    return f"fundamentals:{symbol.upper()}"

def key_portfolio(user_id: int) -> str:
    return f"portfolio:{user_id}"