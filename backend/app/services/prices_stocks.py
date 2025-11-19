import os
import requests
from typing import Optional
from decimal import Decimal

TWELVE_API = "https://api.twelvedata.com"
TIMEOUT = 5

API_KEY = os.getenv("TWELVE_DATA_API_KEY")


def _to_decimal(value) -> Optional[Decimal]:

    if value is None:
        return None
    try:
        return Decimal(str(value))
    except:
        return None


def get_stock_price(symbol: str, interval: str = "1min") -> Optional[Decimal]:
    # Get the latest stock price

    if not symbol:
        return None

    if not API_KEY:
        return None

    try:
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "outputsize": 1,
            "format": "JSON",
            "apikey": API_KEY,
        }

        r = requests.get(
            f"{TWELVE_API}/time_series",
            params=params,
            timeout=TIMEOUT
        )
        r.raise_for_status()

        data = r.json()


        if data.get("status") == "error":
            return None

        values = data.get("values")
        if not values:
            return None

        latest = values[0]

        close = latest.get("close")
        if close is None:
            return None

        # Return decimal
        return _to_decimal(close)

    except requests.RequestException:
        return None

    except (KeyError, TypeError, ValueError):
        return None
