# services/economic_service.py
import os
import requests
import asyncio
from typing import Optional, Dict, Any, List
from decimal import Decimal
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

FINNHUB_API = "https://finnhub.io/api/v1"
TIMEOUT = 10
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

@dataclass
class EconomicIndicator:
    indicator_code: str
    indicator_name: str
    country: str
    frequency: str
    current_value: Decimal
    previous_value: Decimal
    unit: str
    last_update_date: datetime
    next_update_date: datetime

@dataclass
class EconomicEvent:
    event_id: str
    event_name: str
    country: str
    importance: str
    event_date: datetime
    actual_value: Decimal
    forecast_value: Decimal
    previous_value: Decimal

class EconomicService:
    def __init__(self):
        self._session = requests.Session()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except:
            return None

    def _to_datetime(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        try:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif isinstance(value, (int, float)):
                return datetime.fromtimestamp(value)
            return None
        except:
            return None

    async def _finnhub_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        if not FINNHUB_API_KEY:
            logger.error("Finnhub API key not configured")
            return None

        try:
            params = params.copy()
            params["token"] = FINNHUB_API_KEY
            
            response = self._session.get(
                f"{FINNHUB_API}/{endpoint}",
                params=params,
                timeout=TIMEOUT
            )
            
            if response.status_code == 429:
                logger.warning("Finnhub rate limit exceeded")
                return None
                
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Finnhub economic request failed: {e}")
            return None

    async def get_economic_calendar(self, start_date: datetime = None, end_date: datetime = None) -> List[EconomicEvent]:
        """Obtener calendario económico"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now() + timedelta(days=30)

        params = {
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d")
        }

        data = await self._finnhub_request("calendar/economic", params)
        if not data or "economicCalendar" not in data:
            return []

        events = []
        for event_data in data["economicCalendar"]:
            events.append(EconomicEvent(
                event_id=event_data.get("id", ""),
                event_name=event_data.get("event", ""),
                country=event_data.get("country", ""),
                importance=event_data.get("importance", 1),  # 1=low, 2=medium, 3=high
                event_date=self._to_datetime(event_data.get("time")),
                actual_value=self._to_decimal(event_data.get("actual")),
                forecast_value=self._to_decimal(event_data.get("forecast")),
                previous_value=self._to_decimal(event_data.get("previous"))
            ))

        return events

    async def get_economic_indicator(self, indicator_code: str, country: str = "US") -> Optional[EconomicIndicator]:
        """Obtener indicador económico específico"""
        # Finnhub no tiene endpoint directo para esto, usaríamos calendario
        # Esto es un placeholder para implementación futura
        return None

# Instancia global
_economic_service = EconomicService()

# API pública
async def get_economic_calendar(start_date: datetime = None, end_date: datetime = None) -> List[EconomicEvent]:
    async with _economic_service as service:
        return await service.get_economic_calendar(start_date, end_date)