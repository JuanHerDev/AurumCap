# services/stocks/stock_service.py
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from app.models.stocks.stock_models import StockProfile
import os

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self, db: Session):
        self.db = db
        self.base_currency = "USD"
        
        # API Keys - should be in environment variables
        self.twelvedata_api_key = os.getenv('TWELVEDATA_API_KEY', 'demo')
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY', 'demo')
        
        # Base URLs
        self.twelvedata_base_url = "https://api.twelvedata.com"
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        
        # Cache for frequent operations
        self._price_cache = {}
        self._profile_cache = {}
        self._cache_duration = timedelta(minutes=5)
        
        # Common stock mappings for major exchanges
        self.common_stock_mappings = {
            # US Stocks
            'AAPL': 'NASDAQ', 'MSFT': 'NASDAQ', 'GOOGL': 'NASDAQ', 'AMZN': 'NASDAQ',
            'TSLA': 'NASDAQ', 'META': 'NASDAQ', 'NVDA': 'NASDAQ', 'NFLX': 'NASDAQ',
            'AMD': 'NASDAQ', 'INTC': 'NASDAQ', 'CSCO': 'NASDAQ', 'ADBE': 'NASDAQ',
            
            # NYSE Stocks
            'JPM': 'NYSE', 'JNJ': 'NYSE', 'V': 'NYSE', 'PG': 'NYSE',
            'UNH': 'NYSE', 'HD': 'NYSE', 'DIS': 'NYSE', 'VZ': 'NYSE',
            'KO': 'NYSE', 'WMT': 'NYSE', 'XOM': 'NYSE', 'CVX': 'NYSE',
            
            # ETFs
            'SPY': 'NYSE', 'QQQ': 'NASDAQ', 'VTI': 'NYSE', 'IVV': 'NYSE',
            'VOO': 'NYSE', 'IWM': 'NYSE', 'GLD': 'NYSE', 'SLV': 'NYSE',
            
            # International (sample)
            'BABA': 'NYSE',  # Alibaba
            'TSM': 'NYSE',   # TSMC
            'ASML': 'NASDAQ' # ASML
        }
    
    async def get_current_price(self, symbol: str, exchange: str = None) -> Optional[Dict[str, Any]]:
        """
        Get current stock price using TwelveData API
        """
        symbol_upper = symbol.upper()
        
        # Check cache first
        cache_key = f"price_{symbol_upper}"
        if cache_key in self._price_cache:
            cached_data, timestamp = self._price_cache[cache_key]
            if datetime.now() - timestamp < self._cache_duration:
                return cached_data
        
        try:
            # Determine exchange if not provided
            if not exchange:
                exchange = self._get_exchange_from_symbol(symbol_upper)
            
            # Build API parameters
            params = {
                'symbol': symbol_upper,
                'apikey': self.twelvedata_api_key
            }
            
            if exchange and exchange != 'NASDAQ':  # TwelveData handles NASDAQ by default
                params['symbol'] = f"{symbol_upper}/{exchange}"
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.twelvedata_base_url}/price"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'price' in data and data['price'] != '':
                            price_data = {
                                'symbol': symbol_upper,
                                'price': float(data['price']),
                                'exchange': exchange,
                                'currency': self.base_currency,
                                'last_updated': datetime.now(),
                                'source': 'twelvedata'
                            }
                            
                            # Cache the result
                            self._price_cache[cache_key] = (price_data, datetime.now())
                            return price_data
                        else:
                            logger.warning(f"No price data in response for {symbol_upper}")
                    else:
                        logger.error(f"TwelveData API error for {symbol_upper}: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting stock price for {symbol_upper}: {str(e)}")
            return None
    
    async def get_real_time_quote(self, symbol: str, exchange: str = None) -> Optional[Dict[str, Any]]:
        """
        Get real-time stock quote with detailed information using FinnHub
        """
        symbol_upper = symbol.upper()
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/quote"
                params = {
                    'symbol': symbol_upper,
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('c', 0) > 0:  # Current price exists
                            return {
                                'symbol': symbol_upper,
                                'current_price': data.get('c'),
                                'change': data.get('d'),
                                'percent_change': data.get('dp'),
                                'high_price': data.get('h'),
                                'low_price': data.get('l'),
                                'open_price': data.get('o'),
                                'previous_close': data.get('pc'),
                                'timestamp': datetime.fromtimestamp(data.get('t', 0)),
                                'source': 'finnhub'
                            }
                        else:
                            logger.warning(f"No valid quote data for {symbol_upper}")
                    else:
                        logger.error(f"FinnHub API error for {symbol_upper}: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting real-time quote for {symbol_upper}: {str(e)}")
            return None
    
    async def get_stock_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive stock profile information
        """
        symbol_upper = symbol.upper()
        
        # Check cache first
        cache_key = f"profile_{symbol_upper}"
        if cache_key in self._profile_cache:
            cached_data, timestamp = self._profile_cache[cache_key]
            if datetime.now() - timestamp < self._cache_duration:
                return cached_data
        
        try:
            # Try to get from database first
            db_profile = self._get_stock_profile_from_db(symbol_upper)
            if db_profile and db_profile.cache_until > datetime.now():
                return self._format_db_profile(db_profile)
            
            # If not in DB or cache expired, fetch from APIs
            profile_data = await self._fetch_stock_profile(symbol_upper)
            if profile_data:
                # Save to database
                self._save_stock_profile(profile_data)
                # Update cache
                self._profile_cache[cache_key] = (profile_data, datetime.now())
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error getting stock profile for {symbol_upper}: {str(e)}")
            return None
    
    async def _fetch_stock_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch stock profile from FinnHub API
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/stock/profile2"
                params = {
                    'symbol': symbol,
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and 'name' in data:
                            return {
                                'symbol': symbol,
                                'company_name': data.get('name', ''),
                                'description': data.get('description', ''),
                                'sector': data.get('finnhubIndustry', ''),
                                'industry': data.get('finnhubIndustry', ''),
                                'country': data.get('country', ''),
                                'currency': data.get('currency', 'USD'),
                                'exchange': data.get('exchange', ''),
                                'market_cap': data.get('marketCapitalization'),
                                'employees': data.get('employees'),
                                'website': data.get('weburl', ''),
                                'logo_url': data.get('logo', ''),
                                'ipo_date': datetime.fromisoformat(data['ipo']) if data.get('ipo') else None,
                                'last_updated': datetime.now(),
                                'cache_until': datetime.now() + timedelta(hours=24),
                                'source': 'finnhub'
                            }
                        else:
                            logger.warning(f"No profile data for {symbol}")
                    else:
                        logger.error(f"FinnHub profile API error for {symbol}: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching stock profile for {symbol}: {str(e)}")
            return None
    
    async def get_historical_data(self, symbol: str, interval: str = '1day', 
                                 start_date: str = None, end_date: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical stock data using TwelveData
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'apikey': self.twelvedata_api_key,
                'outputsize': 100  # Limit to 100 data points
            }
            
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.twelvedata_base_url}/time_series"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'ok' and 'values' in data:
                            historical_data = []
                            for value in data['values']:
                                historical_data.append({
                                    'datetime': datetime.fromisoformat(value['datetime']),
                                    'open': float(value['open']),
                                    'high': float(value['high']),
                                    'low': float(value['low']),
                                    'close': float(value['close']),
                                    'volume': int(value.get('volume', 0))
                                })
                            
                            return historical_data
                        else:
                            logger.warning(f"No historical data for {symbol}: {data.get('message', 'Unknown error')}")
                    else:
                        logger.error(f"TwelveData historical API error for {symbol}: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return None
    
    async def get_fundamental_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental data for a stock
        """
        try:
            # Get multiple fundamental metrics
            metrics = await asyncio.gather(
                self._get_company_metrics(symbol),
                self._get_earnings_data(symbol),
                self._get_dividends_data(symbol),
                return_exceptions=True
            )
            
            fundamental_data = {
                'symbol': symbol.upper(),
                'last_updated': datetime.now()
            }
            
            # Process metrics
            for metric in metrics:
                if isinstance(metric, dict):
                    fundamental_data.update(metric)
            
            return fundamental_data
            
        except Exception as e:
            logger.error(f"Error getting fundamental data for {symbol}: {str(e)}")
            return None
    
    async def _get_company_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Get company financial metrics
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/stock/metric"
                params = {
                    'symbol': symbol.upper(),
                    'metric': 'all',
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('metric', {})
                    else:
                        logger.warning(f"FinnHub metrics API error for {symbol}: {response.status}")
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting company metrics for {symbol}: {str(e)}")
            return {}
    
    async def _get_earnings_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get earnings data for a stock
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/stock/earnings"
                params = {
                    'symbol': symbol.upper(),
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'earnings': data}
                    else:
                        logger.warning(f"FinnHub earnings API error for {symbol}: {response.status}")
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting earnings data for {symbol}: {str(e)}")
            return {}
    
    async def _get_dividends_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get dividends data for a stock
        """
        try:
            # Use TwelveData for dividends
            params = {
                'symbol': symbol.upper(),
                'apikey': self.twelvedata_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.twelvedata_base_url}/dividends"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'dividends': data.get('dividends', [])}
                    else:
                        logger.warning(f"TwelveData dividends API error for {symbol}: {response.status}")
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting dividends data for {symbol}: {str(e)}")
            return {}
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for stocks by company name or symbol
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/search"
                params = {
                    'q': query,
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for result in data.get('result', [])[:10]:  # Limit to 10 results
                            results.append({
                                'symbol': result.get('symbol'),
                                'description': result.get('description'),
                                'display_symbol': result.get('displaySymbol'),
                                'type': result.get('type'),
                                'currency': result.get('currency', 'USD')
                            })
                        
                        return results
                    else:
                        logger.error(f"FinnHub search API error: {response.status}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching stocks for '{query}': {str(e)}")
            return []
    
    async def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status and indices
        """
        try:
            # Major market indices
            indices = ['SPY', 'QQQ', 'DIA', 'IWM', 'VIX']
            
            # Get prices for all indices
            index_prices = await asyncio.gather(
                *[self.get_current_price(index) for index in indices],
                return_exceptions=True
            )
            
            market_status = {
                'last_updated': datetime.now(),
                'indices': {}
            }
            
            for i, index in enumerate(indices):
                price_data = index_prices[i]
                if isinstance(price_data, dict):
                    market_status['indices'][index] = price_data
            
            return market_status
            
        except Exception as e:
            logger.error(f"Error getting market status: {str(e)}")
            return {}
    
    # Helper methods
    def _get_exchange_from_symbol(self, symbol: str) -> str:
        """Get exchange from symbol using common mappings"""
        return self.common_stock_mappings.get(symbol.upper(), 'NASDAQ')
    
    def _get_stock_profile_from_db(self, symbol: str):
        """Get stock profile from database"""
        try:
            return self.db.query(StockProfile).filter(
                StockProfile.symbol == symbol
            ).first()
        except Exception as e:
            logger.error(f"Error getting stock profile from DB for {symbol}: {str(e)}")
            return None
    
    def _save_stock_profile(self, profile_data: Dict[str, Any]):
        """Save stock profile to database"""
        try:
        
            # Remove fields that do not exist in the model
            filtered_data = {k: v for k, v in profile_data.items() 
                            if k in ['symbol', 'company_name', 'description', 'sector', 
                                    'industry', 'country', 'currency', 'exchange', 
                                    'market_cap', 'employees', 'website', 'logo_url', 
                                    'ipo_date', 'last_updated', 'cache_until']}
        
            existing_profile = self.db.query(StockProfile).filter(
                StockProfile.symbol == filtered_data['symbol']
            ).first()
        
            if existing_profile:
                # Update existing profile
                for key, value in filtered_data.items():
                    if hasattr(existing_profile, key):
                        setattr(existing_profile, key, value)
                existing_profile.last_updated = datetime.now()
            else:
                # Create new profile
                new_profile = StockProfile(**filtered_data)
                self.db.add(new_profile)
        
            self.db.commit()
            logger.info(f"✅ Stock profile saved to DB: {filtered_data['symbol']}")
        
        except Exception as e:
            logger.error(f"❌ Error saving stock profile: {str(e)}")
            self.db.rollback()
    
    def _format_db_profile(self, db_profile) -> Dict[str, Any]:
        """Format database profile to API response format"""
        return {
            'symbol': db_profile.symbol,
            'company_name': db_profile.company_name,
            'description': db_profile.description,
            'sector': db_profile.sector,
            'industry': db_profile.industry,
            'country': db_profile.country,
            'currency': db_profile.currency,
            'exchange': db_profile.exchange,
            'market_cap': db_profile.market_cap,
            'employees': db_profile.employees,
            'website': db_profile.website,
            'logo_url': db_profile.logo_url,
            'ipo_date': db_profile.ipo_date,
            'last_updated': db_profile.last_updated,
            'source': 'database'
        }
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Get prices for multiple stocks efficiently"""
        price_tasks = [self.get_current_price(symbol) for symbol in symbols]
        prices = await asyncio.gather(*price_tasks, return_exceptions=True)
        
        results = {}
        for i, symbol in enumerate(symbols):
            price_data = prices[i]
            if isinstance(price_data, dict):
                results[symbol.upper()] = price_data
        
        return results