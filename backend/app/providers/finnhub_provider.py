import asyncio
from dataclasses import dataclass
from typing import Optional
import finnhub
from app.core.settings import settings

# Dataclasses response

@dataclass
class CompanyProfile:
    symbol: str
    name: str
    exchange: str
    industry: str
    website: Optional[str]
    logo: Optional[str]
    market_cap: Optional[float]
    shares_outstanding: Optional[float]
    ipo_date: Optional[str]
    currency: str

@dataclass
class CompanyFundamentals:
    symbol: str
    # Valuation
    pe_ratio: Optional[float]          # Price / Earnings
    pb_ratio: Optional[float]          # Price / Book
    ps_ratio: Optional[float]          # Price / Sales
    ev_ebitda: Optional[float]         # EV / EBITDA
    # Profitability
    roe: Optional[float]               # Return on Equity
    roa: Optional[float]               # Return on Assets
    net_margin: Optional[float]        # Net margin
    gross_margin: Optional[float]      # Gross margin
    # Growth
    revenue_growth_yoy: Optional[float]
    eps_growth_yoy: Optional[float]
    # Dividends
    dividend_yield: Optional[float]
    dividend_per_share: Optional[float]
    # Balance
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    # Price
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    beta: Optional[float]

@dataclass
class CompanyNews:
    headline: str
    summary: str
    url: str
    source: str
    datetime: int                      # Unix timestamp
    image: Optional[str]


# Provider

class FinnhubProvider:
    """
    Async wrapper for the official Finnhub synchronous client.
    Use `asynciio.to_thread` to avoid blocking the FastAPI event loop.
    """

    def __init__(self):
        self._client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)

    # Synchronic Methods

    def _get_profile_sync(self, symbol: str) -> Optional[CompanyProfile]:

        try:
            data = self._client.company_profile2(symbol=symbol)

            if not data:
                return None
            
            return CompanyProfile(
                symbol=symbol,
                name=data.get("name", ""),
                exchange=data.get("exchange", ""),
                industry=data.get("finnhubIndustry", ""),
                website=data.get("weburl"),
                logo=data.get("logo"),
                market_cap=data.get("marketCapitalization"),
                shares_outstanding=data.get("shareOutstanding"),
                ipo_date=data.get("ipo"),
                currency=data.get("currency", "USD"),
            )
        
        except Exception:
            return None
        
    def _get_fundamentals_sync(self, symbol: str) -> Optional[CompanyFundamentals]:

        try:
            data = self._client.company_basic_financials(symbol, "all")

            if not data or not data.get("metric"):
                return None

            m = data["metric"]

            return CompanyFundamentals(
                symbol=symbol,
                # Valuation
                pe_ratio=m.get("peNormalizedAnnual"),
                pb_ratio=m.get("pbAnnual"),
                ps_ratio=m.get("psAnnual"),
                ev_ebitda=m.get("evEbitdaAnnual"),
                # Profitability
                roe=m.get("roeRfy"),
                roa=m.get("roaRfy"),
                net_margin=m.get("netProfitMarginAnnual"),
                gross_margin=m.get("grossMarginAnnual"),
                # Growth
                revenue_growth_yoy=m.get("revenueGrowthAnnual"),
                eps_growth_yoy=m.get("epsGrowth3Y"),
                # Dividends
                dividend_yield=m.get("currentDividendYieldTTM"),
                dividend_per_share=m.get("dividendsPerShareAnnual"),
                # Balance
                debt_to_equity=m.get("totalDebt/totalEquityAnnual"),
                current_ratio=m.get("currentRatioAnnual"),
                # Price
                week_52_high=m.get("52WeekHigh"),
                week_52_low=m.get("52WeekLow"),
                beta=m.get("beta"),
            )
        
        except Exception:
            return None
        
    def _get_news_sync(self, symbol: str, from_date: str, to_date: str) -> list[CompanyNews]:

        try:
            items = self._client.company_news(symbol, _from=from_date, to=to_date)

            if not items:
                return []
            
            return [
                CompanyNews(
                    headline=item.get("headline", ""),
                    summary=item.get("summary", ""),
                    url=item.get("url", ""),
                    source=item.get("source", ""),
                    datetime=item.get("datetime", 0),
                    image=item.get("image"),
                )
                for item in items[20] # Limit 20 responses per request
            ]
        
        except Exception:
            return []
        
    # Public methods async

    async def get_profile(self, symbol: str) -> Optional[CompanyProfile]:
        """ Company profile: name, industry, market cap, logo """
        return await asyncio.to_thread(self._get_profile_sync, symbol.upper())

    async def get_fundamentals(self, symbol: str) -> Optional[CompanyFundamentals]:
        """ Financial metrics: P/E, P/B, ROE, margins, beta, 52w high/low """
        return await asyncio.to_thread(self._get_fundamentals_sync, symbol.upper())

    async def get_news(self, symbol: str, from_date: str, to_date: str) -> list[CompanyNews]:
        """ Recent company news within the given date range """
        return await asyncio.to_thread(self._get_news_sync, symbol.upper(), from_date, to_date)
    
# Global instance 
finnhub_provider = FinnhubProvider()