import os
import requests
from typing import Optional, Dict
from decimal import Decimal

FINNHUB_API = "https://finnhub.io/api/v1"
TIMEOUT = 5
API_KEY = os.getenv("FINNHUB_API_KEY")


def _to_decimal(value):

    if value is None:
        return None
    try:
        return Decimal(str(value))
    except:
        return None


def get_company_profile(symbol: str) -> Optional[Dict]:
    # Get a company profile

    if not symbol or not API_KEY:
        return None

    try:
        params = {"symbol": symbol.upper(), "token": API_KEY}
        r = requests.get(
            f"{FINNHUB_API}/stock/profile2",
            params=params,
            timeout=TIMEOUT
        )
        r.raise_for_status()

        data = r.json()
        if not data or "name" not in data:
            return None

        # filter fields
        return {
            "name": data.get("name"),
            "country": data.get("country"),
            "currency": data.get("currency"),
            "marketCapitalization": _to_decimal(data.get("marketCapitalization")),
            "exchange": data.get("exchange"),
            "finnhubIndustry": data.get("finnhubIndustry"),
        }

    except requests.RequestException:
        return None


def get_company_metrics(symbol: str) -> Optional[Dict]:
    # Get financial metrics from Finnhub

    if not symbol or not API_KEY:
        return None

    try:
        params = {"symbol": symbol.upper(), "token": API_KEY}
        r = requests.get(
            f"{FINNHUB_API}/stock/metric",
            params=params,
            timeout=TIMEOUT
        )
        r.raise_for_status()

        data = r.json()
        metrics = data.get("metric")

        if not metrics:
            return None

        # Convert numeric values to decimal
        cleaned = {}
        for key, value in metrics.items():
            if isinstance(value, (int, float, str)):
                cleaned[key] = _to_decimal(value)
            else:
                cleaned[key] = value

        return cleaned

    except requests.RequestException:
        return None

def get_fundamentals(symbol: str) -> Optional[Dict]:
    # Return a company profile with their financial metrics
    
    if not symbol:
        return None

    profile = get_company_profile(symbol)
    metrics = get_company_metrics(symbol)

    if not profile and not metrics:
        return None

    return {
        "profile": profile,
        "metrics": metrics,
    }
