import os
import requests
from typing import Optional
from decimal import Decimal

COINGECKO_API = "https://api.coingecko.com/api/v3"
TIMEOUT = 5  # seconds


def _to_decimal(value) -> Optional[Decimal]:
    """Convierte valores numéricos de la API a Decimal de forma segura."""
    if value is None:
        return None
    try:
        return Decimal(str(value)) 
    except:
        return None


def get_crypto_price(symbol: str, vs_currency: str = "usd") -> Optional[Decimal]:
    # Get the actual price using CoinGecko
    # First try with symbol, if not works search by name instead

    if not symbol:
        return None

    s = symbol.strip().lower()

    try:
        # Direct try
        r = requests.get(
            f"{COINGECKO_API}/simple/price",
            params={"ids": s, "vs_currencies": vs_currency},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()

        if data and s in data and vs_currency in data[s]:
            return _to_decimal(data[s][vs_currency])

        # Fallback: search symbol
        resp = requests.get(
            f"{COINGECKO_API}/search",
            params={"query": symbol},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        search = resp.json()

        for coin in search.get("coins", []):
            if coin.get("symbol", "").lower() == s or coin.get("id", "").lower() == s:

                coin_id = coin.get("id")

                r2 = requests.get(
                    f"{COINGECKO_API}/simple/price",
                    params={"ids": coin_id, "vs_currencies": vs_currency},
                    timeout=TIMEOUT,
                )
                r2.raise_for_status()
                d2 = r2.json()

                if d2 and coin_id in d2 and vs_currency in d2[coin_id]:
                    return _to_decimal(d2[coin_id][vs_currency])

    except requests.RequestException:
        return None

    return None
