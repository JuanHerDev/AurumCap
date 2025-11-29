# services/crypto/enhanced_crypto_service.py
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import time
from sqlalchemy.orm import Session
from pycoingecko import CoinGeckoAPI

logger = logging.getLogger(__name__)

class EnhancedCryptoService:
    def __init__(self, db: Session):
        self.db = db
        self.cg = CoinGeckoAPI()
        self.base_currency = "usd"
        self.timeout = 30
        self.max_retries = 3
        
        # Cache for frequent searches
        self._search_cache = {}
        self._cache_duration = timedelta(hours=1)
        
        # Extended mappings for common cryptocurrencies
        self.extended_mappings = {
            # Major cryptocurrencies
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'ADA': 'cardano', 'DOT': 'polkadot',
            'LINK': 'chainlink', 'LTC': 'litecoin', 'BCH': 'bitcoin-cash', 'XRP': 'ripple',
            'SOL': 'solana', 'AVAX': 'avalanche-2', 'MATIC': 'matic-network', 
            'DOGE': 'dogecoin', 'ATOM': 'cosmos', 'XLM': 'stellar', 'EOS': 'eos',
            'BNB': 'binancecoin', 'USDT': 'tether', 'USDC': 'usd-coin', 'DAI': 'dai',
            'UNI': 'uniswap', 'AAVE': 'aave', 'MKR': 'maker', 'COMP': 'compound-governance-token',
            'YFI': 'yearn-finance', 'SNX': 'havven', 'CRV': 'curve-dao-token', 
            'SUSHI': 'sushi', '1INCH': '1inch', 'REN': 'republic-protocol', 
            'BAL': 'balancer', 'KNC': 'kyber-network', 'ZRX': '0x',
            
            # Meme coins
            'SHIB': 'shiba-inu', 'PEPE': 'pepe', 'FLOKI': 'floki', 'BONK': 'bonk',
            
            # Layer 2 solutions
            'ARB': 'arbitrum', 'OP': 'optimism', 'METIS': 'metis-token',
            
            # AI tokens
            'TAO': 'bittensor', 'RNDR': 'render-token', 'AKT': 'akash-network',
            
            # DeFi tokens
            'GMX': 'gmx', 'SNX': 'synthetix-network-token', 'CRV': 'curve-dao-token',
            
            # Gaming tokens
            'SAND': 'the-sandbox', 'MANA': 'decentraland', 'GALA': 'gala',
            
            # Oracle tokens
            'BAND': 'band-protocol', 'TRB': 'tellor',
        }

    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price for a cryptocurrency"""
        try:
            coin_id = self._get_coin_id_from_symbol(symbol)
            if not coin_id:
                logger.warning(f"No coin_id found for symbol: {symbol}")
                return None
            
            logger.info(f"Fetching price for {symbol} (coin_id: {coin_id})")
            
            # Use simple price method from CoinGecko
            data = self.cg.get_price(
                ids=coin_id, 
                vs_currencies=self.base_currency, 
                include_market_cap=True, 
                include_24hr_vol=True,
                include_24hr_change=True, 
                include_last_updated_at=True
            )
            
            logger.debug(f"CoinGecko response for {symbol}: {data}")
            
            if coin_id in data and data[coin_id].get(self.base_currency) is not None:
                price_data = {
                    'symbol': symbol.upper(),
                    'coin_id': coin_id,
                    'price': data[coin_id][self.base_currency],
                    'market_cap': data[coin_id].get(f'{self.base_currency}_market_cap'),
                    'volume_24h': data[coin_id].get(f'{self.base_currency}_24h_vol'),
                    'price_change_24h': data[coin_id].get(f'{self.base_currency}_24h_change'),
                    'last_updated': datetime.fromtimestamp(data[coin_id].get('last_updated_at', time.time()))
                }
                logger.info(f"Price obtained for {symbol}: ${price_data['price']}")
                return price_data
            else:
                logger.warning(f"No price data found for {symbol} in response")
                return None
                
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return None

    def _get_coin_id_from_symbol(self, symbol: str) -> Optional[str]:
        """Get CoinGecko ID from symbol with multiple fallback strategies"""
        symbol_upper = symbol.upper()
        
        try:
            # First strategy: Check extended mappings (fastest)
            if symbol_upper in self.extended_mappings:
                coin_id = self.extended_mappings[symbol_upper]
                logger.debug(f"Found in mappings: {symbol_upper} -> {coin_id}")
                return coin_id
            
            # Second strategy: Check database
            try:
                from app.models.crypto.crypto_models import CryptoSymbolMapping
                mapping = self.db.query(CryptoSymbolMapping).filter(
                    CryptoSymbolMapping.symbol == symbol_upper,
                    CryptoSymbolMapping.is_active == True
                ).first()
                
                if mapping:
                    logger.debug(f"Found in database: {symbol_upper} -> {mapping.coingecko_id}")
                    return mapping.coingecko_id
            except Exception as db_error:
                logger.debug(f"Error querying database for {symbol_upper}: {str(db_error)}")
            
            # Third strategy: Search via CoinGecko API
            logger.info(f"Searching for {symbol_upper} via CoinGecko API...")
            search_results = self.cg.search(symbol_upper)
            coins = search_results.get('coins', [])
            
            if coins:
                coin_id = coins[0]['id']
                logger.debug(f"Found via API search: {symbol_upper} -> {coin_id}")
                return coin_id
            
            logger.warning(f"No coin_id found for symbol: {symbol_upper}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting coin ID for {symbol_upper}: {str(e)}")
            return self.extended_mappings.get(symbol_upper)
    
    async def universal_crypto_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Universal search for any cryptocurrency by name, symbol, or ID
        """
        query = query.strip().upper()
        
        # Check cache first for performance
        cache_key = f"search_{query}"
        if cache_key in self._search_cache:
            cached_data, timestamp = self._search_cache[cache_key]
            if datetime.now() - timestamp < self._cache_duration:
                return cached_data
        
        try:
            # Strategy 1: Direct search with CoinGecko API
            search_results = self.cg.search(query)
            coins = search_results.get('coins', [])
            
            formatted_results = []
            for coin in coins[:15]:  # Limit to 15 most relevant results
                coin_id = coin.get('id')
                symbol = coin.get('symbol', '').upper()
                
                # Get real-time market data for each result
                market_data = await self._get_quick_market_data(coin_id)
                
                result = {
                    'coin_id': coin_id,
                    'name': coin.get('name'),
                    'symbol': symbol,
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'thumb': coin.get('thumb'),
                    'large': coin.get('large'),
                    'score': coin.get('score', 0),
                    'market_data': market_data
                }
                formatted_results.append(result)
            
            # Strategy 2: If no results from API, check extended mappings
            if not formatted_results and query in self.extended_mappings:
                coin_id = self.extended_mappings[query]
                coin_data = await self._get_coin_basic_info(coin_id)
                if coin_data:
                    formatted_results.append(coin_data)
            
            # Cache results for future requests
            self._search_cache[cache_key] = (formatted_results, datetime.now())
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in universal search for '{query}': {str(e)}")
            return []
    
    async def _get_quick_market_data(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Get quick market data for search results"""
        try:
            price_data = self.cg.get_price(
                ids=coin_id,
                vs_currencies=self.base_currency,
                include_24hr_change=True,
                include_market_cap=True
            )
            
            if coin_id in price_data:
                return {
                    'current_price': price_data[coin_id].get(self.base_currency),
                    'price_change_24h': price_data[coin_id].get(f'{self.base_currency}_24h_change'),
                    'market_cap': price_data[coin_id].get(f'{self.base_currency}_market_cap')
                }
            return None
            
        except Exception as e:
            logger.debug(f"Could not get market data for {coin_id}: {str(e)}")
            return None
    
    async def _get_coin_basic_info(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Get basic information for a cryptocurrency"""
        try:
            coin_data = self.cg.get_coin_by_id(coin_id)
            return {
                'coin_id': coin_id,
                'name': coin_data.get('name'),
                'symbol': coin_data.get('symbol', '').upper(),
                'market_cap_rank': coin_data.get('market_cap_rank'),
                'thumb': coin_data.get('image', {}).get('thumb'),
                'large': coin_data.get('image', {}).get('large'),
                'score': 1.0,
                'market_data': {
                    'current_price': coin_data.get('market_data', {}).get('current_price', {}).get(self.base_currency),
                    'price_change_24h': coin_data.get('market_data', {}).get('price_change_24h', {}).get(self.base_currency),
                    'market_cap': coin_data.get('market_data', {}).get('market_cap', {}).get(self.base_currency)
                }
            }
        except Exception as e:
            logger.error(f"Error getting basic info for {coin_id}: {str(e)}")
            return None
    
    def get_any_crypto_info(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for ANY cryptocurrency using symbol, name, or CoinGecko ID
        """
        identifier = identifier.strip().lower()
        
        try:
            # Strategy 1: Check extended mappings first (fastest)
            for symbol, coin_id in self.extended_mappings.items():
                if identifier == symbol.lower() or identifier == coin_id.lower():
                    try:
                        coin_data = self.cg.get_coin_by_id(coin_id)
                        return self._format_coin_data(coin_data)
                    except Exception as e:
                        logger.debug(f"Error getting {coin_id} from mappings: {str(e)}")
                        continue

            # Strategy 2: Try to get directly by ID
            try:
                coin_data = self.cg.get_coin_by_id(identifier)
                return self._format_coin_data(coin_data)
            except Exception as e:
                logger.debug(f"Not found by direct ID {identifier}: {str(e)}")

            # Strategy 3: Broad search via CoinGecko API
            search_results = self.cg.search(identifier)
            coins = search_results.get('coins', [])

            if coins:
                # Take the first (most relevant) result
                coin_id = coins[0]['id']
                try:
                    coin_data = self.cg.get_coin_by_id(coin_id)
                    return self._format_coin_data(coin_data)
                except Exception as e:
                    logger.error(f"Error getting coin data for {coin_id}: {str(e)}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting info for '{identifier}': {str(e)}")
            return None
    
    def _format_coin_data(self, coin_data: Dict) -> Dict[str, Any]:
        """Format coin data into a standardized structure"""
        if not coin_data:
            return None

        market_data = coin_data.get('market_data', {})

        # Safely extract nested data with proper type checking
        current_price = market_data.get('current_price', {})
        market_cap = market_data.get('market_cap', {})
        total_volume = market_data.get('total_volume', {})
        price_change_24h = market_data.get('price_change_24h', {})
        price_change_percentage_24h = market_data.get('price_change_percentage_24h', {})
        price_change_percentage_7d = market_data.get('price_change_percentage_7d', {})
        price_change_percentage_30d = market_data.get('price_change_percentage_30d', {})
        price_change_percentage_1y = market_data.get('price_change_percentage_1y', {})
        ath_data = market_data.get('ath', {})
        ath_change_percentage_data = market_data.get('ath_change_percentage', {})
        ath_date_data = market_data.get('ath_date', {})
        atl_data = market_data.get('atl', {})
        atl_change_percentage_data = market_data.get('atl_change_percentage', {})
        atl_date_data = market_data.get('atl_date', {})
        
        return {
            'id': coin_data.get('id'),
            'symbol': coin_data.get('symbol', '').upper(),
            'name': coin_data.get('name'),
            'description': coin_data.get('description', {}).get('en', ''),
            'current_price': current_price.get(self.base_currency) if isinstance(current_price, dict) else current_price,
            'market_cap': market_cap.get(self.base_currency) if isinstance(market_cap, dict) else market_cap,
            'market_cap_rank': coin_data.get('market_cap_rank'),
            'total_volume': total_volume.get(self.base_currency) if isinstance(total_volume, dict) else total_volume,
            'price_change_24h': price_change_24h.get(self.base_currency) if isinstance(price_change_24h, dict) else price_change_24h,
            'price_change_percentage_24h': price_change_percentage_24h.get(self.base_currency) if isinstance(price_change_percentage_24h, dict) else price_change_percentage_24h,
            'price_change_percentage_7d': price_change_percentage_7d.get(self.base_currency) if isinstance(price_change_percentage_7d, dict) else price_change_percentage_7d,
            'price_change_percentage_30d': price_change_percentage_30d.get(self.base_currency) if isinstance(price_change_percentage_30d, dict) else price_change_percentage_30d,
            'price_change_percentage_1y': price_change_percentage_1y.get(self.base_currency) if isinstance(price_change_percentage_1y, dict) else price_change_percentage_1y,
            'circulating_supply': market_data.get('circulating_supply'),
            'total_supply': market_data.get('total_supply'),
            'max_supply': market_data.get('max_supply'),
            'ath': ath_data.get(self.base_currency) if isinstance(ath_data, dict) else ath_data,
            'ath_change_percentage': ath_change_percentage_data.get(self.base_currency) if isinstance(ath_change_percentage_data, dict) else ath_change_percentage_data,
            'ath_date': ath_date_data.get(self.base_currency) if isinstance(ath_date_data, dict) else ath_date_data,
            'atl': atl_data.get(self.base_currency) if isinstance(atl_data, dict) else atl_data,
            'atl_change_percentage': atl_change_percentage_data.get(self.base_currency) if isinstance(atl_change_percentage_data, dict) else atl_change_percentage_data,
            'atl_date': atl_date_data.get(self.base_currency) if isinstance(atl_date_data, dict) else atl_date_data,
            'last_updated': market_data.get('last_updated'),
            'image': coin_data.get('image', {}),
            'links': coin_data.get('links', {}),
            'genesis_date': coin_data.get('genesis_date'),
            'sentiment_votes_up_percentage': coin_data.get('sentiment_votes_up_percentage'),
            'sentiment_votes_down_percentage': coin_data.get('sentiment_votes_down_percentage'),
        }

    # Additional methods for compatibility with existing services
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Get prices for multiple cryptocurrencies"""
        results = {}
        for symbol in symbols:
            price_data = self.get_current_price(symbol)
            if price_data:
                results[symbol.upper()] = price_data
        return results

    def get_sparkline_data(self, symbol: str, days: int = 7) -> Optional[List[float]]:
        """Get sparkline data for simple charts"""
        try:
            historical_data = self.get_historical_data(symbol, days, 'daily')
            if historical_data:
                return [point['price'] for point in historical_data]
            return None
        except Exception as e:
            logger.error(f"Error getting sparkline data for {symbol}: {str(e)}")
            return None

    def get_historical_data(self, symbol: str, days: int = 30, interval: str = 'daily') -> Optional[List[Dict]]:
        """Get historical price data for a cryptocurrency"""
        try:
            coin_id = self._get_coin_id_from_symbol(symbol)
            if not coin_id:
                return None
            
            historical_data = self.cg.get_coin_market_chart_by_id(
                id=coin_id, 
                vs_currency=self.base_currency, 
                days=days, 
                interval=interval
            )
            
            prices = historical_data.get('prices', [])
            formatted_data = []
            
            for price_point in prices:
                formatted_data.append({
                    'timestamp': datetime.fromtimestamp(price_point[0] / 1000),
                    'price': price_point[1]
                })
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return None

    def get_global_market_data(self) -> Optional[Dict[str, Any]]:
        """Get global cryptocurrency market data"""
        try:
            global_data = self.cg.get_global()
            
            return {
                'total_market_cap': global_data.get('total_market_cap', {}).get(self.base_currency),
                'total_volume': global_data.get('total_volume', {}).get(self.base_currency),
                'market_cap_percentage': global_data.get('market_cap_percentage', {}),
                'active_cryptocurrencies': global_data.get('active_cryptocurrencies'),
                'upcoming_icos': global_data.get('upcoming_icos'),
                'ongoing_icos': global_data.get('ongoing_icos'),
                'ended_icos': global_data.get('ended_icos'),
                'markets': global_data.get('markets'),
                'last_updated': global_data.get('updated_at')
            }
            
        except Exception as e:
            logger.error(f"Error getting global market data: {str(e)}")
            return None

    def get_trending_coins(self) -> Optional[List[Dict[str, Any]]]:
        """Get trending cryptocurrencies"""
        try:
            trending = self.cg.get_search_trending()
            trending_coins = []
            
            for coin in trending.get('coins', []):
                coin_data = coin.get('item', {})
                trending_coins.append({
                    'coin_id': coin_data.get('id'),
                    'name': coin_data.get('name'),
                    'symbol': coin_data.get('symbol'),
                    'market_cap_rank': coin_data.get('market_cap_rank'),
                    'thumb': coin_data.get('thumb'),
                    'price_btc': coin_data.get('price_btc')
                })
            
            return trending_coins
            
        except Exception as e:
            logger.error(f"Error getting trending coins: {str(e)}")
            return None

    def search_coins(self, query: str) -> List[Dict[str, Any]]:
        """Search coins by name or symbol"""
        try:
            results = self.cg.search(query)
            coins = results.get('coins', [])
            
            formatted_results = []
            for coin in coins[:10]:  # Limit to 10 results
                formatted_results.append({
                    'coin_id': coin.get('id'),
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'thumb': coin.get('thumb'),
                    'large': coin.get('large')
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching coins for query '{query}': {str(e)}")
            return []