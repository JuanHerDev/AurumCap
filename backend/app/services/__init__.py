# services/__init__.py
from .crypto_service import (
    get_crypto_profile,
    get_crypto_price_data,
    get_crypto_prices_batch,
    get_crypto_historical_data,
    get_crypto_categories
)

from .stock_service import (
    get_stock_profile,
    get_stock_fundamentals,
    get_stock_price,
    get_stock_earnings_calendar
)

from .economic_service import (
    get_economic_calendar
)

from .fundamentals import get_fundamentals
from .prices_crypto import get_crypto_price_sync, get_crypto_details_sync
from .prices_stocks import get_stock_price as get_stock_price_legacy

__all__ = [
    # Crypto
    "get_crypto_profile",
    "get_crypto_price_data", 
    "get_crypto_prices_batch",
    "get_crypto_historical_data",
    "get_crypto_categories",
    
    # Stocks
    "get_stock_profile",
    "get_stock_fundamentals", 
    "get_stock_price",
    "get_stock_earnings_calendar",
    
    # Economic
    "get_economic_calendar",
    
    # Legacy
    "get_fundamentals",
    "get_crypto_price_sync",
    "get_crypto_details_sync", 
    "get_stock_price_legacy"
]