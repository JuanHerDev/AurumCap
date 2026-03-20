from app.providers.massive_provider import massive_provider
from app.schemas.market import MarketStatusResponse
from app.core.cache import cache_get, cache_set, key_market_status, TTL_MARKET_STATUS

# Readable descriptions for the frontend
_STATUS_DESCRIPTIONS = {
    "open":           "Market is open",
    "extended-hours": "Extended hours trading (pre-market or after-hours)",
    "closed":         "Market is closed",
    "unknown":        "Market status unavailable",
}


async def get_market_status() -> MarketStatusResponse:

    # 1. Check cache — market status changes at most a few times per day
    cached = await cache_get(key_market_status())
    if cached:
        return MarketStatusResponse(**cached)

    # 2. Fetch from Massive provider
    status = await massive_provider.get_market_status()

    response = MarketStatusResponse(
        status=status,
        description=_STATUS_DESCRIPTIONS.get(status, "Market status unavailable"),
    )

    # 3. Store in cache for TTL_MARKET_STATUS seconds (60s)
    await cache_set(key_market_status(), response.model_dump(), TTL_MARKET_STATUS)

    return response