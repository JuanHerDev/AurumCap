"""
Enhanced Fundamentals Service
Provides real fundamental data from multiple sources including Yahoo Finance, FinnHub, and Alpha Vantage
Uses PostgreSQL (Supabase) for caching and data persistence
"""

import asyncio
import aiohttp
import yfinance as yf
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
import os

logger = logging.getLogger(__name__)

class ImprovedFundamentalsService:
    """
    Service for retrieving and managing fundamental data from multiple real sources
    """
    
    def __init__(self, db: Session):
        """
        Initialize the fundamentals service
        
        Args:
            db: SQLAlchemy database session for PostgreSQL (Supabase)
        """
        self.db = db
        
        # API Keys from environment variables
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY', 'demo')
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        
        # API endpoints
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        
        # Enhanced cache configuration for better performance
        self._fundamentals_cache = {}
        self._sector_cache = {}
        self._calendar_cache = {}
        
        # Cache durations for different data types
        self.cache_durations = {
            'current_fundamentals': timedelta(hours=6),
            'historical_fundamentals': timedelta(days=1),
            'sector_metrics': timedelta(days=7),
            'economic_calendar': timedelta(hours=12),
            'earnings_calendar': timedelta(hours=6)
        }

    async def get_current_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get enhanced current fundamental data with multiple REAL API sources
        
        Args:
            symbol: Stock symbol (e.g., AAPL, MSFT)
        
        Returns:
            Dictionary containing current fundamental data or None if not found
        """
        symbol_upper = symbol.upper()
        
        # Check memory cache first for better performance
        cache_key = f"current_{symbol_upper}"
        if cache_key in self._fundamentals_cache:
            cached_data, timestamp = self._fundamentals_cache[cache_key]
            if datetime.now() - timestamp < self.cache_durations['current_fundamentals']:
                logger.info(f"Using memory cache for {symbol_upper}")
                return cached_data
        
        try:
            # Try database first with cache validation
            db_fundamentals = self._get_current_fundamentals_from_db(symbol_upper)
            if db_fundamentals and db_fundamentals.cache_until > datetime.now():
                logger.info(f"Using database cache for {symbol_upper}")
                fundamentals_data = self._format_current_fundamentals(db_fundamentals)
                self._fundamentals_cache[cache_key] = (fundamentals_data, datetime.now())
                return fundamentals_data
            
            # Try multiple REAL data sources in order of preference
            fundamentals_data = await self._fetch_from_multiple_real_sources(symbol_upper)
            
            if not fundamentals_data:
                logger.error(f"All real data sources failed for {symbol_upper}")
                # Return database data even if expired as fallback
                if db_fundamentals:
                    logger.info(f"Using expired database data as fallback for {symbol_upper}")
                    return self._format_current_fundamentals(db_fundamentals)
                return None
            
            # Save to database for future requests
            self._save_current_fundamentals(fundamentals_data)
            
            # Update memory cache
            self._fundamentals_cache[cache_key] = (fundamentals_data, datetime.now())
            logger.info(f"Successfully retrieved and saved REAL fundamentals for {symbol_upper}")
            
            return fundamentals_data
            
        except Exception as e:
            logger.error(f"Error getting current fundamentals for {symbol_upper}: {str(e)}")
            # Return database data as fallback even on error
            db_fundamentals = self._get_current_fundamentals_from_db(symbol_upper)
            if db_fundamentals:
                return self._format_current_fundamentals(db_fundamentals)
            return None

    async def _fetch_from_multiple_real_sources(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Try multiple REAL data sources in sequence with fallback strategy
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Fundamental data from the first successful source
        """
        # Define sources in order of preference
        sources = [
            self._fetch_finnhub_fundamentals,
            self._fetch_alpha_vantage_fundamentals,
            self._fetch_yahoo_finance_fundamentals  # Yahoo Finance as fallback (no API key required)
        ]
        
        for source in sources:
            try:
                logger.info(f"Trying {source.__name__} for {symbol}")
                data = await source(symbol)
                if data and self._validate_real_fundamentals_data(data):
                    logger.info(f"Successfully fetched REAL data for {symbol} from {source.__name__}")
                    return data
                else:
                    logger.warning(f"Invalid data from {source.__name__} for {symbol}")
            except Exception as e:
                logger.warning(f"Source {source.__name__} failed for {symbol}: {str(e)}")
                continue
        
        return None

    def _validate_real_fundamentals_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate that fundamentals data has REAL financial data
        
        Args:
            data: Fundamental data dictionary
        
        Returns:
            Boolean indicating if data is valid
        """
        if not data or not isinstance(data, dict):
            return False
        
        # Must have symbol
        if not data.get('symbol'):
            return False
        
        # Check if we have at least some meaningful financial data
        financial_fields = ['pe_ratio', 'eps', 'market_cap', 'revenue', 'net_income', 'price_to_book']
        financial_data_count = sum(1 for field in financial_fields if data.get(field) is not None)
        
        # We need at least 2 financial fields to consider data valid
        return financial_data_count >= 2

    async def _fetch_finnhub_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch REAL fundamentals from FinnHub API - Primary data source
        
        Args:
            symbol: Stock symbol
        
        Returns:
            FinnHub fundamental data or None if failed
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Try company profile first
                profile_url = f"{self.finnhub_base_url}/stock/profile2"
                profile_params = {'symbol': symbol, 'token': self.finnhub_api_key}
                
                profile_data = {}
                try:
                    async with session.get(profile_url, params=profile_params) as response:
                        if response.status == 200:
                            profile_data = await response.json()
                            logger.debug(f"FinnHub profile data for {symbol}: {profile_data}")
                        elif response.status == 429:
                            logger.warning(f"FinnHub rate limit exceeded for {symbol}")
                            return None
                        else:
                            logger.warning(f"FinnHub profile API error for {symbol}: {response.status}")
                except asyncio.TimeoutError:
                    logger.warning(f"FinnHub profile API timeout for {symbol}")
                    return None
                
                # Try company metrics
                metrics_url = f"{self.finnhub_base_url}/stock/metric"
                metrics_params = {'symbol': symbol, 'metric': 'all', 'token': self.finnhub_api_key}
                
                metrics_data = {}
                try:
                    async with session.get(metrics_url, params=metrics_params) as response:
                        if response.status == 200:
                            metrics_data = await response.json()
                            logger.debug(f"FinnHub metrics data for {symbol}: {metrics_data}")
                        elif response.status == 429:
                            logger.warning(f"FinnHub rate limit exceeded for {symbol}")
                            return None
                        else:
                            logger.warning(f"FinnHub metrics API error for {symbol}: {response.status}")
                except asyncio.TimeoutError:
                    logger.warning(f"FinnHub metrics API timeout for {symbol}")
                    return None
                
                # Check if we got any meaningful data
                has_metrics = bool(metrics_data and 'metric' in metrics_data)
                has_profile = bool(profile_data and 'name' in profile_data)
                
                if not has_metrics and not has_profile:
                    logger.warning(f"No meaningful data from FinnHub for {symbol}")
                    return None
                
                # Build fundamentals with available data
                fundamentals = {
                    'symbol': symbol,
                    'last_updated': datetime.now(),
                    'cache_until': datetime.now() + self.cache_durations['current_fundamentals'],
                    'source': 'finnhub'
                }
                
                # Add profile data if available
                if has_profile:
                    fundamentals.update({
                        'company_name': profile_data.get('name'),
                        'sector': profile_data.get('finnhubIndustry'),
                        'industry': profile_data.get('finnhubIndustry'),
                        'currency': profile_data.get('currency', 'USD'),
                        'country': profile_data.get('country'),
                        'exchange': profile_data.get('exchange'),
                        'ipo_date': self._parse_date(profile_data.get('ipo')),
                        'website': profile_data.get('weburl'),
                    })
                
                # Add metrics data if available
                if has_metrics:
                    metrics = metrics_data['metric']
                    fundamentals.update({
                        'pe_ratio': metrics.get('peNormalizedAnnual'),
                        'eps': metrics.get('epsNormalizedAnnual'),
                        'dividend_yield': metrics.get('dividendYieldIndicatedAnnual'),
                        'market_cap': metrics.get('marketCapitalization'),
                        'year_high': metrics.get('52WeekHigh'),
                        'year_low': metrics.get('52WeekLow'),
                        'volume_avg': metrics.get('volume30DayAvg'),
                        'price_to_book': metrics.get('pbAnnual'),
                        'price_to_sales': metrics.get('psAnnual'),
                        'profit_margin': metrics.get('netMarginAnnual'),
                    })
                
                return fundamentals
                
        except Exception as e:
            logger.error(f"FinnHub API error for {symbol}: {str(e)}")
            return None

    async def _fetch_alpha_vantage_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch REAL fundamentals from Alpha Vantage API - Secondary data source
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Alpha Vantage fundamental data or None if failed
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Get overview data from Alpha Vantage
                overview_url = self.alpha_vantage_base_url
                overview_params = {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.alpha_vantage_api_key
                }
                
                try:
                    async with session.get(overview_url, params=overview_params) as response:
                        if response.status == 200:
                            overview_data = await response.json()
                            
                            # Check for API limits or errors
                            if 'Error Message' in overview_data:
                                logger.warning(f"Alpha Vantage error for {symbol}: {overview_data['Error Message']}")
                                return None
                            if 'Information' in overview_data:
                                logger.warning(f"Alpha Vantage API limit: {overview_data['Information']}")
                                return None
                            if 'Note' in overview_data:
                                logger.warning(f"Alpha Vantage API note: {overview_data['Note']}")
                                return None
                            
                            # Check if we have basic data
                            if not overview_data.get('Symbol'):
                                logger.warning(f"No symbol data from Alpha Vantage for {symbol}")
                                return None
                            
                            logger.debug(f"Alpha Vantage data for {symbol}: received {len(overview_data)} fields")
                            
                            # Parse Alpha Vantage data
                            fundamentals = {
                                'symbol': symbol,
                                'company_name': overview_data.get('Name'),
                                'sector': overview_data.get('Sector'),
                                'industry': overview_data.get('Industry'),
                                'currency': 'USD',
                                'last_updated': datetime.now(),
                                'cache_until': datetime.now() + self.cache_durations['current_fundamentals'],
                                'source': 'alpha_vantage',
                                'pe_ratio': self._safe_float(overview_data.get('PERatio')),
                                'eps': self._safe_float(overview_data.get('EPS')),
                                'dividend_yield': self._safe_float(overview_data.get('DividendYield')),
                                'market_cap': self._safe_int(overview_data.get('MarketCapitalization')),
                                'year_high': self._safe_float(overview_data.get('52WeekHigh')),
                                'year_low': self._safe_float(overview_data.get('52WeekLow')),
                                'profit_margin': self._safe_float(overview_data.get('ProfitMargin')),
                                'total_assets': self._safe_int(overview_data.get('TotalAssets')),
                                'total_liabilities': self._safe_int(overview_data.get('TotalLiabilities')),
                                'revenue': self._safe_int(overview_data.get('RevenueTTM')),
                                'net_income': self._safe_int(overview_data.get('NetIncomeTTM')),
                                'fiscal_year_end': overview_data.get('FiscalYearEnd'),
                                'exchange': overview_data.get('Exchange'),
                                'country': overview_data.get('Country'),
                                'description': overview_data.get('Description'),
                                'price_to_book': self._safe_float(overview_data.get('PriceToBookRatio')),
                                'price_to_sales': self._safe_float(overview_data.get('PriceToSalesRatioTTM')),
                            }
                            
                            return fundamentals
                        else:
                            logger.warning(f"Alpha Vantage API error for {symbol}: {response.status}")
                            return None
                except asyncio.TimeoutError:
                    logger.warning(f"Alpha Vantage API timeout for {symbol}")
                    return None
                        
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {str(e)}")
            return None

    async def _fetch_yahoo_finance_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch REAL fundamentals from Yahoo Finance - Third data source (No API key required)
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Yahoo Finance fundamental data or None if failed
        """
        try:
            # Use yfinance library to get real data from Yahoo Finance
            logger.info(f"Fetching Yahoo Finance data for {symbol}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get stock info
            info = ticker.info
            
            if not info:
                logger.warning(f"No info available from Yahoo Finance for {symbol}")
                return None
            
            # Extract fundamental data
            fundamentals = {
                'symbol': symbol,
                'company_name': info.get('longName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'currency': info.get('currency', 'USD'),
                'last_updated': datetime.now(),
                'cache_until': datetime.now() + self.cache_durations['current_fundamentals'],
                'source': 'yahoo_finance',
                # Valuation metrics
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'eps': info.get('trailingEps'),
                'forward_eps': info.get('forwardEps'),
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                # Price metrics
                'current_price': info.get('currentPrice'),
                'target_mean_price': info.get('targetMeanPrice'),
                'target_high_price': info.get('targetHighPrice'),
                'target_low_price': info.get('targetLowPrice'),
                'year_high': info.get('fiftyTwoWeekHigh'),
                'year_low': info.get('fiftyTwoWeekLow'),
                # Dividend information
                'dividend_yield': info.get('dividendYield'),
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': info.get('payoutRatio'),
                # Financial ratios
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                # Volume and liquidity
                'volume_avg': info.get('averageVolume'),
                'beta': info.get('beta'),
                # Company information
                'exchange': info.get('exchange'),
                'country': info.get('country'),
                'website': info.get('website'),
                'employees': info.get('fullTimeEmployees'),
                'description': info.get('longBusinessSummary'),
            }
            
            logger.info(f"Successfully retrieved Yahoo Finance data for {symbol}")
            return fundamentals
            
        except Exception as e:
            logger.error(f"Yahoo Finance API error for {symbol}: {str(e)}")
            return None

    async def get_historical_fundamentals(self, symbol: str, period_type: str = 'annual', 
                                         limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical fundamental data with REAL data from Yahoo Finance
        
        Args:
            symbol: Stock symbol
            period_type: 'annual' or 'quarterly'
            limit: Number of periods to return
        
        Returns:
            List of historical fundamental data or None if failed
        """
        symbol_upper = symbol.upper()
        
        try:
            # Try database first
            db_historical = self._get_historical_fundamentals_from_db(symbol_upper, period_type, limit)
            if db_historical:
                logger.info(f"Using database historical data for {symbol_upper}")
                return [self._format_historical_fundamentals(item) for item in db_historical]
            
            # Get REAL historical data from Yahoo Finance
            historical_data = await self._fetch_yahoo_historical_data(symbol_upper, period_type, limit)
            
            if historical_data:
                # Save to database for future requests
                for data in historical_data:
                    self._save_historical_fundamentals(data)
                logger.info(f"Retrieved and saved REAL historical data for {symbol_upper}")
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical fundamentals for {symbol}: {str(e)}")
            return None

    async def _fetch_yahoo_historical_data(self, symbol: str, period_type: str,
                                         limit: int) -> List[Dict[str, Any]]:
        """
        Fetch REAL historical fundamental data from Yahoo Finance
        
        Args:
            symbol: Stock symbol
            period_type: 'annual' or 'quarterly'
            limit: Number of periods to fetch
        
        Returns:
            List of historical fundamental data
        """
        try:
            ticker = yf.Ticker(symbol)
            historical_data = []
            
            # Get financial statements based on period type
            if period_type == 'annual':
                financials = ticker.financials
                balance_sheet = ticker.balance_sheet
            else:  # quarterly
                financials = ticker.quarterly_financials
                balance_sheet = ticker.quarterly_balance_sheet
            
            if financials is None or financials.empty:
                logger.warning(f"No financial data available from Yahoo Finance for {symbol}")
                return []
            
            # Process each period
            for i, date in enumerate(financials.columns[:limit]):
                try:
                    # Get basic financial data without recursion
                    eps_value = None
                    try:
                        # Try to get EPS from income statement
                        income_stmt = ticker.income_stmt if period_type == 'annual' else ticker.quarterly_income_stmt
                        if income_stmt is not None and not income_stmt.empty:
                            if 'Basic EPS' in income_stmt.index and date in income_stmt.columns:
                                eps_value = income_stmt.loc['Basic EPS'][date]
                            elif 'Diluted EPS' in income_stmt.index and date in income_stmt.columns:
                                eps_value = income_stmt.loc['Diluted EPS'][date]
                    except:
                        pass
                    
                    historical_entry = {
                        'symbol': symbol,
                        'period_type': period_type,
                        'fiscal_date': date.date(),
                        'report_date': datetime.now(),
                        'revenue': financials.loc['Total Revenue'][date] if 'Total Revenue' in financials.index else None,
                        'net_income': financials.loc['Net Income'][date] if 'Net Income' in financials.index else None,
                        'eps': eps_value,
                        'gross_profit': financials.loc['Gross Profit'][date] if 'Gross Profit' in financials.index else None,
                        'operating_income': financials.loc['Operating Income'][date] if 'Operating Income' in financials.index else None,
                        'ebitda': financials.loc['EBITDA'][date] if 'EBITDA' in financials.index else None,
                        'source': 'yahoo_finance',
                        'is_estimated': False,
                        'created_at': datetime.now()
                    }
                    
                    # Add balance sheet data if available
                    if balance_sheet is not None and not balance_sheet.empty and date in balance_sheet.columns:
                        historical_entry.update({
                            'total_assets': balance_sheet.loc['Total Assets'][date] if 'Total Assets' in balance_sheet.index else None,
                            'total_liabilities': balance_sheet.loc['Total Liabilities'][date] if 'Total Liabilities' in balance_sheet.index else None,
                            'cash': balance_sheet.loc['Cash'][date] if 'Cash' in balance_sheet.index else 
                                   balance_sheet.loc['Cash And Cash Equivalents'][date] if 'Cash And Cash Equivalents' in balance_sheet.index else None,
                            'long_term_debt': balance_sheet.loc['Long Term Debt'][date] if 'Long Term Debt' in balance_sheet.index else None,
                            'shareholders_equity': balance_sheet.loc['Total Stockholder Equity'][date] if 'Total Stockholder Equity' in balance_sheet.index else None,
                        })
                    
                    historical_data.append(historical_entry)
                    
                except Exception as e:
                    logger.warning(f"Error processing historical period {date} for {symbol}: {str(e)}")
                    continue
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance historical data for {symbol}: {str(e)}")
            return []

    async def get_sector_metrics(self, sector: str) -> Optional[Dict[str, Any]]:
        """
        Get enhanced sector metrics with REAL data aggregation
        
        Args:
            sector: Sector name
        
        Returns:
            Sector metrics dictionary or None if failed
        """
        # Check memory cache
        cache_key = f"sector_{sector}"
        if cache_key in self._sector_cache:
            cached_data, timestamp = self._sector_cache[cache_key]
            if datetime.now() - timestamp < self.cache_durations['sector_metrics']:
                return cached_data
        
        try:
            # Try database first
            db_sector = self._get_sector_metrics_from_db(sector)
            if db_sector and db_sector.cache_until > datetime.now():
                sector_data = self._format_sector_metrics(db_sector)
                self._sector_cache[cache_key] = (sector_data, datetime.now())
                return sector_data
            
            # Calculate sector metrics from REAL stock data WITHOUT RECURSION
            sector_data = await self._calculate_real_sector_metrics(sector)
            if sector_data:
                self._save_sector_metrics(sector_data)
                # Update memory cache
                self._sector_cache[cache_key] = (sector_data, datetime.now())
            
            return sector_data
            
        except Exception as e:
            logger.error(f"Error getting sector metrics for {sector}: {str(e)}")
            return None

    async def _calculate_real_sector_metrics(self, sector: str) -> Optional[Dict[str, Any]]:
        """
        Calculate sector metrics from REAL stock data in the sector WITHOUT RECURSION
        
        Args:
            sector: Sector name
        
        Returns:
            Aggregated sector metrics
        """
        try:
            from app.models.stocks.stock_models import StockProfile
            
            # Get stocks in this sector from database
            stocks_in_sector = self.db.query(StockProfile).filter(
                StockProfile.sector == sector
            ).all()
            
            if not stocks_in_sector:
                logger.warning(f"No stocks found for sector: {sector}")
                return None
            
            # Collect REAL fundamentals for all stocks in sector WITHOUT calling get_current_fundamentals
            fundamentals_list = []
            for stock in stocks_in_sector[:5]:  # Limit to 5 stocks for performance
                try:
                    # Use direct Yahoo Finance fetch instead of get_current_fundamentals to avoid recursion
                    fundamentals = await self._fetch_yahoo_finance_fundamentals(stock.symbol)
                    if fundamentals and self._validate_real_fundamentals_data(fundamentals):
                        fundamentals_list.append(fundamentals)
                except Exception as e:
                    logger.warning(f"Error getting fundamentals for {stock.symbol}: {str(e)}")
                    continue
            
            if not fundamentals_list:
                logger.warning(f"No valid fundamentals found for sector: {sector}")
                return None
            
            # Calculate averages from REAL data
            metrics = {
                'sector': sector,
                'avg_pe_ratio': self._calculate_average([f.get('pe_ratio') for f in fundamentals_list]),
                'avg_ps_ratio': self._calculate_average([f.get('price_to_sales') for f in fundamentals_list]),
                'avg_pb_ratio': self._calculate_average([f.get('price_to_book') for f in fundamentals_list]),
                'avg_roe': self._calculate_average([f.get('return_on_equity') for f in fundamentals_list]),
                'avg_profit_margin': self._calculate_average([f.get('profit_margin') for f in fundamentals_list]),
                'avg_dividend_yield': self._calculate_average([f.get('dividend_yield') for f in fundamentals_list]),
                'last_updated': datetime.now(),
                'cache_until': datetime.now() + self.cache_durations['sector_metrics'],
                'stocks_count': len(fundamentals_list),
                'total_market_cap': sum(f.get('market_cap', 0) for f in fundamentals_list if f.get('market_cap')),
                'source': 'real_data_aggregation'
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating real sector metrics for {sector}: {str(e)}")
            return None

    # Database Operations

    def _get_current_fundamentals_from_db(self, symbol: str):
        """
        Get current fundamentals from database
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Database record or None
        """
        try:
            from app.models.fundamentals.fundamental_models import StockFundamentalsCurrent
            return self.db.query(StockFundamentalsCurrent).filter(
                StockFundamentalsCurrent.symbol == symbol
            ).first()
        except Exception as e:
            logger.error(f"Error getting current fundamentals from DB for {symbol}: {str(e)}")
            return None

    def _save_current_fundamentals(self, fundamentals_data: Dict[str, Any]):
        """
        Save current fundamentals to database
        
        Args:
            fundamentals_data: Fundamental data dictionary
        """
        try:
            from app.models.fundamentals.fundamental_models import StockFundamentalsCurrent
            
            # Filter only fields that exist in the model
            model_fields = ['symbol', 'pe_ratio', 'eps', 'dividend_yield', 'market_cap', 
                          'revenue', 'net_income', 'profit_margin', 'total_assets', 
                          'total_liabilities', 'cash', 'year_high', 'year_low', 
                          'volume_avg', 'last_earnings_date', 'next_earnings_date', 
                          'fiscal_year_end', 'last_updated', 'cache_until']
            
            filtered_data = {k: v for k, v in fundamentals_data.items() if k in model_fields}
            
            # Check if record exists
            existing = self.db.query(StockFundamentalsCurrent).filter(
                StockFundamentalsCurrent.symbol == filtered_data['symbol']
            ).first()
            
            if existing:
                # Update existing record
                for key, value in filtered_data.items():
                    setattr(existing, key, value)
                logger.info(f"✅ Updated current fundamentals in DB: {filtered_data['symbol']}")
            else:
                # Create new record
                new_fundamentals = StockFundamentalsCurrent(**filtered_data)
                self.db.add(new_fundamentals)
                logger.info(f"✅ Saved new current fundamentals to DB: {filtered_data['symbol']}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error saving current fundamentals: {str(e)}")
            self.db.rollback()

    def _get_historical_fundamentals_from_db(self, symbol: str, period_type: str, limit: int):
        """
        Get historical fundamentals from database
        
        Args:
            symbol: Stock symbol
            period_type: 'annual' or 'quarterly'
            limit: Number of records to return
        
        Returns:
            List of historical records
        """
        try:
            from app.models.fundamentals.fundamental_models import StockFundamentalsHistorical
            return self.db.query(StockFundamentalsHistorical).filter(
                StockFundamentalsHistorical.symbol == symbol,
                StockFundamentalsHistorical.period_type == period_type
            ).order_by(StockFundamentalsHistorical.fiscal_date.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting historical fundamentals from DB for {symbol}: {str(e)}")
            return None

    def _save_historical_fundamentals(self, historical_data: Dict[str, Any]):
        """
        Save historical fundamentals to database
        
        Args:
            historical_data: Historical data dictionary
        """
        try:
            from app.models.fundamentals.fundamental_models import StockFundamentalsHistorical
            
            # Filter only fields that exist in the model
            model_fields = ['symbol', 'period_type', 'fiscal_date', 'report_date', 'revenue', 
                          'net_income', 'eps', 'total_assets', 'total_liabilities', 
                          'cash', 'pe_ratio', 'profit_margin', 'dividend_yield', 'source', 'is_estimated', 'created_at']
            
            filtered_data = {k: v for k, v in historical_data.items() if k in model_fields}
            
            # Check if record already exists
            existing = self.db.query(StockFundamentalsHistorical).filter(
                StockFundamentalsHistorical.symbol == filtered_data['symbol'],
                StockFundamentalsHistorical.fiscal_date == filtered_data['fiscal_date'],
                StockFundamentalsHistorical.period_type == filtered_data['period_type']
            ).first()
            
            if not existing:
                new_historical = StockFundamentalsHistorical(**filtered_data)
                self.db.add(new_historical)
                self.db.commit()
                logger.info(f"✅ Saved historical fundamentals to DB: {filtered_data['symbol']} for {filtered_data['fiscal_date']}")
            
        except Exception as e:
            logger.error(f"❌ Error saving historical fundamentals: {str(e)}")
            self.db.rollback()

    # Utility Methods

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object
        
        Args:
            date_str: Date string in various formats
        
        Returns:
            datetime object or None
        """
        if not date_str:
            return None
        try:
            if isinstance(date_str, (int, float)):
                return datetime.fromtimestamp(date_str)
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def _safe_float(self, value: Any) -> Optional[float]:
        """
        Safely convert value to float, handling None and string formats
        
        Args:
            value: Input value
        
        Returns:
            Float value or None
        """
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Handle percentage values and formatted numbers
                value = value.replace('%', '').replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """
        Safely convert value to int, handling None and string formats
        
        Args:
            value: Input value
        
        Returns:
            Integer value or None
        """
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Handle formatted numbers with commas
                value = value.replace(',', '')
                # Handle market cap format (e.g., "1.23B" -> 1230000000)
                if 'B' in value:
                    return int(float(value.replace('B', '')) * 1000000000)
                elif 'M' in value:
                    return int(float(value.replace('M', '')) * 1000000)
                elif 'T' in value:
                    return int(float(value.replace('T', '')) * 1000000000000)
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _calculate_average(self, values: List[float]) -> Optional[float]:
        """
        Calculate average of a list, ignoring None values
        
        Args:
            values: List of values
        
        Returns:
            Average value or None
        """
        valid_values = [v for v in values if v is not None]
        if valid_values:
            return sum(valid_values) / len(valid_values)
        return None

    # Placeholder methods for calendar data
    async def get_economic_calendar(self, start_date: str, end_date: str, country: str) -> List[Dict[str, Any]]:
        """Get economic calendar events - to be implemented"""
        return []

    async def get_earnings_calendar(self, start_date: str, end_date: str, symbol: Optional[str]) -> List[Dict[str, Any]]:
        """Get earnings calendar events - to be implemented"""
        return []

    def _get_sector_metrics_from_db(self, sector: str):
        """Get sector metrics from database - to be implemented"""
        return None

    def _format_sector_metrics(self, sector_data):
        """Format sector metrics - to be implemented"""
        return sector_data

    def _save_sector_metrics(self, sector_data: Dict[str, Any]):
        """Save sector metrics to database - to be implemented"""
        pass

    def _format_current_fundamentals(self, db_data):
        """Format current fundamentals from database record"""
        if db_data is None:
            return None
        return {key: getattr(db_data, key) for key in ['symbol', 'pe_ratio', 'eps', 'dividend_yield', 'market_cap', 
                                                      'revenue', 'net_income', 'profit_margin', 'total_assets', 
                                                      'total_liabilities', 'cash', 'year_high', 'year_low', 
                                                      'volume_avg', 'last_earnings_date', 'next_earnings_date', 
                                                      'fiscal_year_end', 'last_updated', 'cache_until'] 
                if hasattr(db_data, key)}

    def _format_historical_fundamentals(self, db_data):
        """Format historical fundamentals from database record"""
        if db_data is None:
            return None
        return {key: getattr(db_data, key) for key in ['symbol', 'period_type', 'fiscal_date', 'report_date', 'revenue', 
                                                      'net_income', 'eps', 'total_assets', 'total_liabilities', 
                                                      'cash', 'pe_ratio', 'profit_margin', 'dividend_yield', 'source', 'is_estimated', 'created_at']
                if hasattr(db_data, key)}