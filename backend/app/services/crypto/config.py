from app.core.config import settings
from typing import Optional

class CryptoConfig:
    COINGECKO_API_KEY: Optional[str] = None
    BASE_URL: str = "https://api.coingecko.com/api/v3"
    REQUEST_TIMEOUT: int = 30
    RATE_LIMIT_CALLS: int = 50
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Cache settings
    PRICE_CACHE_TTL: int = 60  # 1 minute for prices
    PROFILE_CACHE_TTL: int = 3600  # 1 hour for profiles
    MARKET_DATA_CACHE_TTL: int = 300  # 5 minutes for market data

crypto_config = CryptoConfig()