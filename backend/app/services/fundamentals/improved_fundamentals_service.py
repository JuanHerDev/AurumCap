# services/fundamentals/improved_fundamentals_service.py
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
import os

logger = logging.getLogger(__name__)

class ImprovedFundamentalsService:
    def __init__(self, db: Session):
        self.db = db
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY', 'demo')
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        
        # Enhanced cache configuration
        self._fundamentals_cache = {}
        self._sector_cache = {}
        self._calendar_cache = {}
        
        self.cache_durations = {
            'current_fundamentals': timedelta(hours=6),
            'historical_fundamentals': timedelta(days=1),
            'sector_metrics': timedelta(days=7),
            'economic_calendar': timedelta(hours=12),
            'earnings_calendar': timedelta(hours=6)
        }

    async def get_current_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get enhanced current fundamental data with multiple API sources
        """
        symbol_upper = symbol.upper()
        
        # Check memory cache first
        cache_key = f"current_{symbol_upper}"
        if cache_key in self._fundamentals_cache:
            cached_data, timestamp = self._fundamentals_cache[cache_key]
            if datetime.now() - timestamp < self.cache_durations['current_fundamentals']:
                return cached_data
        
        try:
            # Try database first
            db_fundamentals = self._get_current_fundamentals_from_db(symbol_upper)
            if db_fundamentals and db_fundamentals.cache_until > datetime.now():
                fundamentals_data = self._format_current_fundamentals(db_fundamentals)
                self._fundamentals_cache[cache_key] = (fundamentals_data, datetime.now())
                return fundamentals_data
            
            # Fetch from multiple FinnHub endpoints
            fundamentals_data = await self._fetch_enhanced_fundamentals(symbol_upper)
            if fundamentals_data:
                # Save to database
                self._save_current_fundamentals(fundamentals_data)
                # Update memory cache
                self._fundamentals_cache[cache_key] = (fundamentals_data, datetime.now())
            
            return fundamentals_data
            
        except Exception as e:
            logger.error(f"Error getting current fundamentals for {symbol_upper}: {str(e)}")
            return None

    async def _fetch_enhanced_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch enhanced fundamental data from multiple FinnHub endpoints
        """
        try:
            # Get data from multiple endpoints concurrently
            metrics_data, quote_data, profile_data = await asyncio.gather(
                self._fetch_company_metrics(symbol),
                self._fetch_stock_quote(symbol),
                self._fetch_company_profile(symbol),
                return_exceptions=True
            )
            
            # Process metrics data
            fundamentals = {
                'symbol': symbol,
                'last_updated': datetime.now(),
                'cache_until': datetime.now() + self.cache_durations['current_fundamentals'],
                'source': 'finnhub'
            }
            
            # Add metrics data
            if isinstance(metrics_data, dict) and 'metric' in metrics_data:
                metrics = metrics_data['metric']
                fundamentals.update(self._parse_metrics_data(metrics))
            
            # Add quote data
            if isinstance(quote_data, dict):
                fundamentals.update(self._parse_quote_data(quote_data))
            
            # Add profile data
            if isinstance(profile_data, dict):
                fundamentals.update(self._parse_profile_data(profile_data))
            
            # Calculate derived metrics
            fundamentals.update(self._calculate_derived_metrics(fundamentals))
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error fetching enhanced fundamentals for {symbol}: {str(e)}")
            return None

    async def _fetch_company_metrics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch company metrics from FinnHub"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/stock/metric"
                params = {
                    'symbol': symbol,
                    'metric': 'all',
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Metrics API error for {symbol}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching metrics for {symbol}: {str(e)}")
            return None

    async def _fetch_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch stock quote from FinnHub"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/quote"
                params = {
                    'symbol': symbol,
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Quote API error for {symbol}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return None

    async def _fetch_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch company profile from FinnHub"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/stock/profile2"
                params = {
                    'symbol': symbol,
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Profile API error for {symbol}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching profile for {symbol}: {str(e)}")
            return None

    def _parse_metrics_data(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Parse metrics data from FinnHub response"""
        return {
            'pe_ratio': metrics.get('peNormalizedAnnual'),
            'eps': metrics.get('epsNormalizedAnnual'),
            'dividend_yield': metrics.get('dividendYieldIndicatedAnnual'),
            'market_cap': metrics.get('marketCapitalization'),
            'revenue': metrics.get('revenuePerShare'),
            'net_income': metrics.get('netIncome'),
            'total_assets': metrics.get('totalAssets'),
            'total_liabilities': metrics.get('totalDebt'),
            'cash': metrics.get('cashAndEquivalents'),
            'year_high': metrics.get('52WeekHigh'),
            'year_low': metrics.get('52WeekLow'),
            'volume_avg': metrics.get('volume30DayAvg'),
            'last_earnings_date': self._parse_date(metrics.get('lastEarningsDate')),
            'next_earnings_date': self._parse_date(metrics.get('nextEarningsDate')),
            'fiscal_year_end': metrics.get('fiscalYearEnd'),
        }

    def _parse_quote_data(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Parse quote data from FinnHub response"""
        return {
            'current_price': quote.get('c'),
            'price_change': quote.get('d'),
            'percent_change': quote.get('dp'),
            'day_high': quote.get('h'),
            'day_low': quote.get('l'),
            'open_price': quote.get('o'),
            'previous_close': quote.get('pc'),
        }

    def _parse_profile_data(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Parse profile data from FinnHub response"""
        return {
            'company_name': profile.get('name'),
            'sector': profile.get('finnhubIndustry'),
            'industry': profile.get('finnhubIndustry'),
            'country': profile.get('country'),
            'currency': profile.get('currency'),
            'exchange': profile.get('exchange'),
            'website': profile.get('weburl'),
            'logo_url': profile.get('logo'),
            'ipo_date': self._parse_date(profile.get('ipo')),
            'employees': profile.get('employees'),
        }

    def _calculate_derived_metrics(self, fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived financial metrics"""
        derived = {}
        
        # Calculate profit margin if we have revenue and net income
        revenue = fundamentals.get('revenue')
        net_income = fundamentals.get('net_income')
        
        if revenue and net_income and revenue > 0:
            derived['profit_margin'] = (net_income / revenue) * 100
        
        # Calculate additional ratios
        market_cap = fundamentals.get('market_cap')
        total_assets = fundamentals.get('total_assets')
        total_liabilities = fundamentals.get('total_liabilities')
        
        if market_cap and total_assets and total_assets > 0:
            derived['price_to_book'] = market_cap / total_assets
        
        if total_assets and total_liabilities and total_assets > 0:
            derived['debt_to_assets'] = (total_liabilities / total_assets) * 100
        
        return derived

    async def get_historical_fundamentals(self, symbol: str, period_type: str = 'annual', 
                                         limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical fundamental data with fallback strategies
        """
        symbol_upper = symbol.upper()
        
        try:
            # Try database first
            db_historical = self._get_historical_fundamentals_from_db(symbol_upper, period_type, limit)
            if db_historical:
                return [self._format_historical_fundamentals(item) for item in db_historical]
            
            # Try FinnHub financials
            historical_data = await self._fetch_finnhub_financials(symbol_upper, period_type, limit)
            if not historical_data:
                # Fallback: Generate from current data
                historical_data = await self._generate_historical_from_current(symbol_upper, period_type, limit)
            
            if historical_data:
                # Save to database
                for data in historical_data:
                    self._save_historical_fundamentals(data)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical fundamentals for {symbol}: {str(e)}")
            return None

    async def _fetch_finnhub_financials(self, symbol: str, period_type: str, 
                                      limit: int) -> Optional[List[Dict[str, Any]]]:
        """Fetch financial statements from FinnHub"""
        try:
            # FinnHub financials endpoint might be premium-only
            # This is a fallback implementation
            return await self._generate_historical_from_current(symbol, period_type, limit)
        except Exception as e:
            logger.error(f"Error fetching FinnHub financials for {symbol}: {str(e)}")
            return None

    async def _generate_historical_from_current(self, symbol: str, period_type: str,
                                              limit: int) -> List[Dict[str, Any]]:
        """Generate historical data from current fundamentals (fallback)"""
        try:
            current_data = await self.get_current_fundamentals(symbol)
            if not current_data:
                return []
            
            # Create historical entries based on current data
            historical_data = []
            base_date = datetime.now()
            
            for i in range(limit):
                historical_date = base_date - timedelta(days=365 * (i + 1))
                
                historical_entry = {
                    'symbol': symbol,
                    'period_type': period_type,
                    'fiscal_date': historical_date.date(),
                    'report_date': historical_date,
                    'revenue': current_data.get('revenue'),
                    'net_income': current_data.get('net_income'),
                    'eps': current_data.get('eps'),
                    'total_assets': current_data.get('total_assets'),
                    'total_liabilities': current_data.get('total_liabilities'),
                    'cash': current_data.get('cash'),
                    'pe_ratio': current_data.get('pe_ratio'),
                    'profit_margin': current_data.get('profit_margin'),
                    'source': 'estimated',
                    'is_estimated': True,
                    'created_at': datetime.now()
                }
                
                historical_data.append(historical_entry)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error generating historical data for {symbol}: {str(e)}")
            return []

    async def get_sector_metrics(self, sector: str) -> Optional[Dict[str, Any]]:
        """
        Get enhanced sector metrics with data population
        """
        # First, ensure we have sector data
        await self._populate_sector_data()
        
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
            
            # Calculate sector metrics
            sector_data = await self._calculate_enhanced_sector_metrics(sector)
            if sector_data:
                # Save to database
                self._save_sector_metrics(sector_data)
                # Update memory cache
                self._sector_cache[cache_key] = (sector_data, datetime.now())
            
            return sector_data
            
        except Exception as e:
            logger.error(f"Error getting sector metrics for {sector}: {str(e)}")
            return None

    async def _populate_sector_data(self):
        """Populate sector data if database is empty"""
        try:
            from app.models.stocks.stock_models import StockProfile
            
            # Check if we have any stock profiles
            stock_count = self.db.query(StockProfile).count()
            
            if stock_count == 0:
                logger.info("Populating initial sector data...")
                # Add some major stocks to get sector data
                major_stocks = [
                    {'symbol': 'AAPL', 'sector': 'Technology'},
                    {'symbol': 'MSFT', 'sector': 'Technology'},
                    {'symbol': 'GOOGL', 'sector': 'Technology'},
                    {'symbol': 'AMZN', 'sector': 'Consumer Cyclical'},
                    {'symbol': 'TSLA', 'sector': 'Automotive'},
                    {'symbol': 'JPM', 'sector': 'Financial Services'},
                    {'symbol': 'JNJ', 'sector': 'Healthcare'},
                    {'symbol': 'XOM', 'sector': 'Energy'},
                ]
                
                for stock_data in major_stocks:
                    # Check if stock exists
                    existing = self.db.query(StockProfile).filter(
                        StockProfile.symbol == stock_data['symbol']
                    ).first()
                    
                    if not existing:
                        new_stock = StockProfile(
                            symbol=stock_data['symbol'],
                            company_name=f"Company {stock_data['symbol']}",
                            sector=stock_data['sector'],
                            currency='USD',
                            exchange='NASDAQ',
                            last_updated=datetime.now(),
                            cache_until=datetime.now() + timedelta(days=30)
                        )
                        self.db.add(new_stock)
                
                self.db.commit()
                logger.info("Initial sector data populated")
                
        except Exception as e:
            logger.error(f"Error populating sector data: {str(e)}")
            self.db.rollback()

    async def _calculate_enhanced_sector_metrics(self, sector: str) -> Optional[Dict[str, Any]]:
        """Calculate enhanced sector metrics"""
        try:
            from app.models.stocks.stock_models import StockProfile
            
            # Get stocks in this sector
            stocks_in_sector = self.db.query(StockProfile).filter(
                StockProfile.sector == sector
            ).all()
            
            if not stocks_in_sector:
                logger.warning(f"No stocks found for sector: {sector}")
                return None
            
            # Get fundamentals for all stocks in sector
            fundamentals_list = []
            for stock in stocks_in_sector:
                fundamentals = await self.get_current_fundamentals(stock.symbol)
                if fundamentals and fundamentals.get('pe_ratio'):
                    fundamentals_list.append(fundamentals)
            
            if not fundamentals_list:
                return None
            
            # Calculate comprehensive metrics
            metrics = {
                'sector': sector,
                'avg_pe_ratio': self._calculate_average([f.get('pe_ratio') for f in fundamentals_list]),
                'avg_ps_ratio': self._calculate_average([f.get('price_to_sales') for f in fundamentals_list]),
                'avg_pb_ratio': self._calculate_average([f.get('price_to_book') for f in fundamentals_list]),
                'avg_debt_to_equity': self._calculate_average([f.get('debt_to_assets') for f in fundamentals_list]),
                'avg_roe': self._calculate_average([f.get('return_on_equity') for f in fundamentals_list]),
                'avg_profit_margin': self._calculate_average([f.get('profit_margin') for f in fundamentals_list]),
                'avg_dividend_yield': self._calculate_average([f.get('dividend_yield') for f in fundamentals_list]),
                'last_updated': datetime.now(),
                'cache_until': datetime.now() + self.cache_durations['sector_metrics'],
                'stocks_count': len(fundamentals_list),
                'total_market_cap': sum(f.get('market_cap', 0) for f in fundamentals_list if f.get('market_cap'))
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating enhanced sector metrics for {sector}: {str(e)}")
            return None

    async def get_economic_calendar(self, start_date: str, end_date: str, 
                                  country: str = 'US') -> Optional[List[Dict[str, Any]]]:
        """
        Get economic calendar with improved date handling
        """
        cache_key = f"calendar_{start_date}_{end_date}_{country}"
        
        # Check memory cache
        if cache_key in self._calendar_cache:
            cached_data, timestamp = self._calendar_cache[cache_key]
            if datetime.now() - timestamp < self.cache_durations['economic_calendar']:
                return cached_data
        
        try:
            # Format dates for API
            from_date = self._format_date_for_api(start_date)
            to_date = self._format_date_for_api(end_date)
            
            calendar_data = await self._fetch_economic_calendar(from_date, to_date, country)
            if calendar_data:
                self._calendar_cache[cache_key] = (calendar_data, datetime.now())
            
            return calendar_data
            
        except Exception as e:
            logger.error(f"Error getting economic calendar: {str(e)}")
            return None

    async def _fetch_economic_calendar(self, start_date: str, end_date: str, 
                                     country: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch economic calendar from FinnHub API
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/calendar/economic"
                params = {
                    'from': start_date,
                    'to': end_date,
                    'token': self.finnhub_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and 'economicCalendar' in data:
                            events = []
                            for event in data['economicCalendar']:
                                if event.get('country') == country:
                                    events.append({
                                        'event_date': self._parse_date(event.get('time')),
                                        'event_type': 'economic',
                                        'country': event.get('country'),
                                        'event_name': event.get('event'),
                                        'importance': event.get('importance'),
                                        'actual': event.get('actual'),
                                        'previous': event.get('previous'),
                                        'forecast': event.get('forecast'),
                                        'unit': event.get('unit'),
                                        'currency': event.get('currency')
                                    })
                            
                            return events
                        else:
                            logger.warning("No economic calendar data found")
                    else:
                        logger.error(f"FinnHub calendar API error: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {str(e)}")
            return None

    async def get_earnings_calendar(self, start_date: str, end_date: str, 
                                  symbol: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get earnings calendar for a date range, optionally filtered by symbol
        """
        try:
            # Fetch from FinnHub API
            earnings_data = await self._fetch_earnings_calendar(start_date, end_date, symbol)
            return earnings_data
            
        except Exception as e:
            logger.error(f"Error getting earnings calendar: {str(e)}")
            return None

    async def _fetch_earnings_calendar(self, start_date: str, end_date: str, 
                                     symbol: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch earnings calendar from FinnHub API
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.finnhub_base_url}/calendar/earnings"
                params = {
                    'from': start_date,
                    'to': end_date,
                    'token': self.finnhub_api_key
                }
                
                if symbol:
                    params['symbol'] = symbol
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and 'earningsCalendar' in data:
                            earnings = []
                            for earning in data['earningsCalendar']:
                                earnings.append({
                                    'event_date': self._parse_date(earning.get('date')),
                                    'event_type': 'earnings',
                                    'symbol': earning.get('symbol'),
                                    'company_name': earning.get('name'),
                                    'eps_estimate': earning.get('epsEstimate'),
                                    'eps_actual': earning.get('epsActual'),
                                    'revenue_estimate': earning.get('revenueEstimate'),
                                    'revenue_actual': earning.get('revenueActual'),
                                    'hour': earning.get('hour'),
                                    'year': earning.get('year'),
                                    'quarter': earning.get('quarter')
                                })
                            
                            return earnings
                        else:
                            logger.warning("No earnings calendar data found")
                    else:
                        logger.error(f"FinnHub earnings calendar API error: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {str(e)}")
            return None

    # Database Operations - MÉTODOS FALTANTES AGREGADOS
    def _get_current_fundamentals_from_db(self, symbol: str):
        """Get current fundamentals from database"""
        try:
            from app.models.fundamentals.fundamental_models import StockFundamentalsCurrent
            return self.db.query(StockFundamentalsCurrent).filter(
                StockFundamentalsCurrent.symbol == symbol
            ).first()
        except Exception as e:
            logger.error(f"Error getting current fundamentals from DB for {symbol}: {str(e)}")
            return None

    def _save_current_fundamentals(self, fundamentals_data: Dict[str, Any]):
        """Save current fundamentals to database"""
        try:
            from app.models.fundamentals.fundamental_models import StockFundamentalsCurrent
            
            # Filter only fields that exist in the model
            model_fields = ['symbol', 'pe_ratio', 'eps', 'dividend_yield', 'market_cap', 
                          'revenue', 'net_income', 'profit_margin', 'total_assets', 
                          'total_liabilities', 'cash', 'year_high', 'year_low', 
                          'volume_avg', 'last_earnings_date', 'next_earnings_date', 
                          'fiscal_year_end', 'last_updated', 'cache_until']
            
            filtered_data = {k: v for k, v in fundamentals_data.items() if k in model_fields}
            
            existing = self.db.query(StockFundamentalsCurrent).filter(
                StockFundamentalsCurrent.symbol == filtered_data['symbol']
            ).first()
            
            if existing:
                # Update existing record
                for key, value in filtered_data.items():
                    setattr(existing, key, value)
            else:
                # Create new record
                new_fundamentals = StockFundamentalsCurrent(**filtered_data)
                self.db.add(new_fundamentals)
            
            self.db.commit()
            logger.info(f"✅ Current fundamentals saved to DB: {filtered_data['symbol']}")
            
        except Exception as e:
            logger.error(f"❌ Error saving current fundamentals: {str(e)}")
            self.db.rollback()

    def _get_historical_fundamentals_from_db(self, symbol: str, period_type: str, limit: int):
        """Get historical fundamentals from database"""
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
        """Save historical fundamentals to database"""
        try:
            from app.models.fundamentals.fundamental_models import StockFundamentalsHistorical
            
            # Filter only fields that exist in the model
            model_fields = ['symbol', 'period_type', 'fiscal_date', 'report_date', 'revenue', 
                          'net_income', 'eps', 'dividends_per_share', 'gross_profit', 
                          'operating_income', 'ebitda', 'total_assets', 'total_liabilities', 
                          'cash', 'long_term_debt', 'shareholders_equity', 'pe_ratio', 
                          'ps_ratio', 'pb_ratio', 'roe', 'debt_to_equity', 'current_ratio', 
                          'profit_margin', 'shares_outstanding', 'market_cap', 'source', 
                          'is_estimated', 'created_at']
            
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
                logger.info(f"✅ Historical fundamentals saved to DB: {filtered_data['symbol']}")
            
        except Exception as e:
            logger.error(f"❌ Error saving historical fundamentals: {str(e)}")
            self.db.rollback()

    def _get_sector_metrics_from_db(self, sector: str):
        """Get sector metrics from database"""
        try:
            from app.models.fundamentals.fundamental_models import SectorMetrics
            return self.db.query(SectorMetrics).filter(
                SectorMetrics.sector == sector
            ).first()
        except Exception as e:
            logger.error(f"Error getting sector metrics from DB for {sector}: {str(e)}")
            return None

    def _save_sector_metrics(self, sector_data: Dict[str, Any]):
        """Save sector metrics to database"""
        try:
            from app.models.fundamentals.fundamental_models import SectorMetrics
            
            # Filter only fields that exist in the model
            model_fields = ['sector', 'avg_pe_ratio', 'avg_ps_ratio', 'avg_pb_ratio', 
                          'avg_debt_to_equity', 'avg_roe', 'avg_profit_margin', 
                          'avg_dividend_yield', 'last_updated', 'cache_until']
            
            filtered_data = {k: v for k, v in sector_data.items() if k in model_fields}
            
            existing = self.db.query(SectorMetrics).filter(
                SectorMetrics.sector == filtered_data['sector']
            ).first()
            
            if existing:
                # Update existing record
                for key, value in filtered_data.items():
                    setattr(existing, key, value)
            else:
                # Create new record
                new_sector = SectorMetrics(**filtered_data)
                self.db.add(new_sector)
            
            self.db.commit()
            logger.info(f"✅ Sector metrics saved to DB: {filtered_data['sector']}")
            
        except Exception as e:
            logger.error(f"❌ Error saving sector metrics: {str(e)}")
            self.db.rollback()

    # Formatting Methods
    def _format_current_fundamentals(self, db_fundamentals) -> Dict[str, Any]:
        """Format database current fundamentals to API response"""
        return {
            'symbol': db_fundamentals.symbol,
            'pe_ratio': db_fundamentals.pe_ratio,
            'eps': db_fundamentals.eps,
            'dividend_yield': db_fundamentals.dividend_yield,
            'market_cap': db_fundamentals.market_cap,
            'revenue': db_fundamentals.revenue,
            'net_income': db_fundamentals.net_income,
            'profit_margin': db_fundamentals.profit_margin,
            'total_assets': db_fundamentals.total_assets,
            'total_liabilities': db_fundamentals.total_liabilities,
            'cash': db_fundamentals.cash,
            'year_high': db_fundamentals.year_high,
            'year_low': db_fundamentals.year_low,
            'volume_avg': db_fundamentals.volume_avg,
            'last_earnings_date': db_fundamentals.last_earnings_date,
            'next_earnings_date': db_fundamentals.next_earnings_date,
            'fiscal_year_end': db_fundamentals.fiscal_year_end,
            'last_updated': db_fundamentals.last_updated,
            'source': 'database'
        }

    def _format_historical_fundamentals(self, db_historical) -> Dict[str, Any]:
        """Format database historical fundamentals to API response"""
        return {
            'symbol': db_historical.symbol,
            'period_type': db_historical.period_type,
            'fiscal_date': db_historical.fiscal_date,
            'report_date': db_historical.report_date,
            'revenue': db_historical.revenue,
            'net_income': db_historical.net_income,
            'eps': db_historical.eps,
            'dividends_per_share': db_historical.dividends_per_share,
            'gross_profit': db_historical.gross_profit,
            'operating_income': db_historical.operating_income,
            'ebitda': db_historical.ebitda,
            'total_assets': db_historical.total_assets,
            'total_liabilities': db_historical.total_liabilities,
            'cash': db_historical.cash,
            'long_term_debt': db_historical.long_term_debt,
            'shareholders_equity': db_historical.shareholders_equity,
            'pe_ratio': db_historical.pe_ratio,
            'ps_ratio': db_historical.ps_ratio,
            'pb_ratio': db_historical.pb_ratio,
            'roe': db_historical.roe,
            'debt_to_equity': db_historical.debt_to_equity,
            'current_ratio': db_historical.current_ratio,
            'profit_margin': db_historical.profit_margin,
            'shares_outstanding': db_historical.shares_outstanding,
            'market_cap': db_historical.market_cap,
            'source': db_historical.source,
            'is_estimated': db_historical.is_estimated
        }

    def _format_sector_metrics(self, db_sector) -> Dict[str, Any]:
        """Format database sector metrics to API response"""
        return {
            'sector': db_sector.sector,
            'avg_pe_ratio': db_sector.avg_pe_ratio,
            'avg_ps_ratio': db_sector.avg_ps_ratio,
            'avg_pb_ratio': db_sector.avg_pb_ratio,
            'avg_debt_to_equity': db_sector.avg_debt_to_equity,
            'avg_roe': db_sector.avg_roe,
            'avg_profit_margin': db_sector.avg_profit_margin,
            'avg_dividend_yield': db_sector.avg_dividend_yield,
            'last_updated': db_sector.last_updated,
            'source': 'database'
        }

    # Utility Methods
    def _format_date_for_api(self, date_str: str) -> str:
        """Format date for API calls"""
        try:
            # Convert YYYY-MM-DD to Unix timestamp
            dt = datetime.fromisoformat(date_str)
            return str(int(dt.timestamp()))
        except:
            return date_str

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        try:
            if isinstance(date_str, (int, float)):
                return datetime.fromtimestamp(date_str)
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def _calculate_average(self, values: List[float]) -> Optional[float]:
        """Calculate average of a list, ignoring None values"""
        valid_values = [v for v in values if v is not None]
        if valid_values:
            return sum(valid_values) / len(valid_values)
        return None