from app.providers.massive_provider import massive_provider
from app.schemas.market import MarketStatusResponse

# Readable descriptions for the frontend
_STATUS_DESCRIPTIONS = {
    "open":           "Market is open",
    "extended-hours": "Extended hours trading (pre-market or after-hours)",
    "closed":         "Market is closed",
    "unknown":        "Market status unavailable",
}


async def get_market_status() -> MarketStatusResponse:
    status = await massive_provider.get_market_status()

    return MarketStatusResponse(
        status=status,
        description=_STATUS_DESCRIPTIONS.get(status, "Market status unavailable"),
    )