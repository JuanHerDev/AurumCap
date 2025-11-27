# services/stock_service.py
import os
import requests
import asyncio
from typing import Optional, Dict, Any, List
from decimal import Decimal
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# APIs
TWELVE_API = "https://api.twelvedata.com"
FINNHUB_API = "https://finnhub.io/api/v1"
TIMEOUT = 10

# API Keys
TWELVE_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

@dataclass
class StockProfileData:
    symbol: str
    company_name: str
    description: str
    sector: str
    industry: str
    country: str
    currency: str
    exchange: str
    market_cap: Decimal
    employees: int
    website: str
    logo_url: str
    ipo_date: datetime
    last_updated: datetime

@dataclass
class StockFundamentalsData:
    symbol: str
    pe_ratio: Decimal
    eps: Decimal
    dividend_yield: Decimal
    market_cap: Decimal
    revenue: Decimal
    net_income: Decimal
    profit_margin: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    cash: Decimal
    year_high: Decimal
    year_low: Decimal
    volume_avg: Decimal
    last_earnings_date: datetime
    next_earnings_date: datetime
    fiscal_year_end: str
    last_updated: datetime

@dataclass
class StockPriceData:
    symbol: str
    price: Decimal
    change: Decimal
    change_percentage: Decimal
    volume: Decimal
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    previous_close: Decimal

class StockService:
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

    # ==================== TWELVEDATA METHODS ====================
    
    async def _twelvedata_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Request a TwelveData API"""
        if not TWELVE_API_KEY:
            logger.error("TwelveData API key not configured")
            return None

        try:
            params = params.copy()
            params["apikey"] = TWELVE_API_KEY
            
            response = self._session.get(
                f"{TWELVE_API}/{endpoint}",
                params=params,
                timeout=TIMEOUT
            )
            
            if response.status_code == 429:
                logger.warning("TwelveData rate limit exceeded")
                return None
                
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "error":
                logger.error(f"TwelveData API error: {data.get('message')}")
                return None
                
            return data
            
        except requests.RequestException as e:
            logger.error(f"TwelveData request failed: {e}")
            return None

    async def get_stock_profile_twelvedata(self, symbol: str) -> Optional[StockProfileData]:
        """Obtener perfil de stock desde TwelveData"""
        params = {
            "symbol": symbol.upper(),
        }
        
        data = await self._twelvedata_request("profile", params)
        if not data:
            return None

        return StockProfileData(
            symbol=data.get("symbol", "").upper(),
            company_name=data.get("name", ""),
            description="",  # TwelveData no tiene descripción
            sector=data.get("sector", ""),
            industry=data.get("industry", ""),
            country=data.get("country", ""),
            currency=data.get("currency", ""),
            exchange=data.get("exchange", ""),
            market_cap=self._to_decimal(data.get("market_capitalization")),
            employees=data.get("employees", 0),
            website=data.get("website", ""),
            logo_url="",  # TwelveData no tiene logo
            ipo_date=self._to_datetime(data.get("ipo_date")),
            last_updated=datetime.now()
        )

    async def get_stock_price_twelvedata(self, symbol: str) -> Optional[StockPriceData]:
        """Obtener precio actual desde TwelveData"""
        params = {
            "symbol": symbol.upper(),
            "interval": "1min",
            "outputsize": 1
        }
        
        data = await self._twelvedata_request("time_series", params)
        if not data or "values" not in data:
            return None

        values = data["values"][0]
        meta = data.get("meta", {})
        
        return StockPriceData(
            symbol=meta.get("symbol", "").upper(),
            price=self._to_decimal(values.get("close")),
            change=self._to_decimal(values.get("close")) - self._to_decimal(values.get("previous_close")),
            change_percentage=(self._to_decimal(values.get("close")) - self._to_decimal(values.get("previous_close"))) / self._to_decimal(values.get("previous_close")) * 100,
            volume=self._to_decimal(values.get("volume")),
            timestamp=self._to_datetime(values.get("datetime")),
            open=self._to_decimal(values.get("open")),
            high=self._to_decimal(values.get("high")),
            low=self._to_decimal(values.get("low")),
            previous_close=self._to_decimal(values.get("previous_close"))
        )

    # ==================== FINNHUB METHODS ====================
    
    async def _finnhub_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Request a Finnhub API"""
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
            logger.error(f"Finnhub request failed: {e}")
            return None

    async def get_stock_profile_finnhub(self, symbol: str) -> Optional[StockProfileData]:
        """Obtener perfil completo desde Finnhub"""
        data = await self._finnhub_request("stock/profile2", {"symbol": symbol.upper()})
        if not data:
            return None

        return StockProfileData(
            symbol=symbol.upper(),
            company_name=data.get("name", ""),
            description="",  # Finnhub no tiene descripción en profile
            sector=data.get("finnhubIndustry", ""),
            industry=data.get("finnhubIndustry", ""),  # Finnhub usa mismo campo
            country=data.get("country", ""),
            currency=data.get("currency", ""),
            exchange=data.get("exchange", ""),
            market_cap=self._to_decimal(data.get("marketCapitalization")),
            employees=data.get("employees", 0),
            website=data.get("weburl", ""),
            logo_url=data.get("logo", ""),
            ipo_date=self._to_datetime(data.get("ipo")),
            last_updated=datetime.now()
        )

    async def get_stock_fundamentals_finnhub(self, symbol: str) -> Optional[StockFundamentalsData]:
        """Obtener fundamentales desde Finnhub"""
        data = await self._finnhub_request("stock/metric", {"symbol": symbol.upper(), "metric": "all"})
        if not data or "metric" not in data:
            return None

        metric = data["metric"]
        
        return StockFundamentalsData(
            symbol=symbol.upper(),
            pe_ratio=self._to_decimal(metric.get("peNormalizedAnnual")),
            eps=self._to_decimal(metric.get("epsNormalizedAnnual")),
            dividend_yield=self._to_decimal(metric.get("dividendYieldIndicatedAnnual")),
            market_cap=self._to_decimal(metric.get("marketCapitalization")),
            revenue=self._to_decimal(metric.get("revenuePerShareAnnual")),
            net_income=self._to_decimal(metric.get("netIncomePerShareAnnual")),
            profit_margin=self._to_decimal(metric.get("profitMarginAnnual")),
            total_assets=self._to_decimal(metric.get("totalAssets")),
            total_liabilities=self._to_decimal(metric.get("totalLiabilities")),
            cash=self._to_decimal(metric.get("cashPerShare")),
            year_high=self._to_decimal(metric.get("52WeekHigh")),
            year_low=self._to_decimal(metric.get("52WeekLow")),
            volume_avg=self._to_decimal(metric.get("volume30DayAvg")),
            last_earnings_date=None,  # Necesitaría endpoint separado
            next_earnings_date=None,
            fiscal_year_end="December",  # Asumido, necesitaría más datos
            last_updated=datetime.now()
        )

    async def get_earnings_calendar(self, symbol: str) -> Optional[Dict]:
        """Obtener calendario de earnings"""
        data = await self._finnhub_request("calendar/earnings", {"symbol": symbol.upper()})
        if not data or "earningsCalendar" not in data:
            return None
            
        return data["earningsCalendar"]

    # ==================== COMBINED METHODS ====================
    
    async def get_complete_stock_profile(self, symbol: str) -> Optional[StockProfileData]:
        """Combinar datos de TwelveData y Finnhub para perfil completo"""
        # Primero intentar con Finnhub (mejor data)
        finnhub_profile = await self.get_stock_profile_finnhub(symbol)
        if finnhub_profile:
            return finnhub_profile
            
        # Fallback a TwelveData
        return await self.get_stock_profile_twelvedata(symbol)

    async def get_complete_fundamentals(self, symbol: str) -> Optional[StockFundamentalsData]:
        """
        Get fundamentals combining multiple sources
        """
        try:
            # First get from Finnhub
            finnhub_data = await self.get_stock_fundamentals_finnhub(symbol)

            # If Finnhub haven't dividend yield, try with TwelveData
            if finnhub_data and (finnhub_data.dividend_yield is None or finnhub_data.dividend_yield == 0):
                try:
                    twelve_data = await self._twelvedata_request("quote", {"symbol": symbol})

                    if twelve_data and "dividend_yield" in twelve_data:
                        dividend_yield = self._to_decimal(twelve_data['dividend_yield'])
                        if dividend_yield and dividend_yield > 0:
                            finnhub_data.dividend_yield = dividend_yield
                            logger.info(f"✅ Fixed dividend yield for {symbol}: {dividend_yield}")
                except Exception as e:
                    logger.warning(f"Could not get dividend yield from TwelveData for {symbol}: {e}")
                        
                    return finnhub_data
                    
        except Exception as e:
            logger.error(f"Error getting complete fundamentals for {symbol}: {e}")
            return None

    async def get_stock_price_combined(self, symbol: str) -> Optional[StockPriceData]:
        """Obtener precio combinando fuentes"""
        # Preferir TwelveData para precios
        price_data = await self.get_stock_price_twelvedata(symbol)
        return price_data

# Instancia global
_stock_service = StockService()

# API pública
async def get_stock_profile(symbol: str) -> Optional[StockProfileData]:
    async with _stock_service as service:
        return await service.get_complete_stock_profile(symbol)

async def get_stock_fundamentals(symbol: str) -> Optional[StockFundamentalsData]:
    async with _stock_service as service:
        return await service.get_complete_fundamentals(symbol)

async def get_stock_price(symbol: str) -> Optional[StockPriceData]:
    async with _stock_service as service:
        return await service.get_stock_price_combined(symbol)

async def get_stock_earnings_calendar(symbol: str) -> Optional[Dict]:
    async with _stock_service as service:
        return await service.get_earnings_calendar(symbol)