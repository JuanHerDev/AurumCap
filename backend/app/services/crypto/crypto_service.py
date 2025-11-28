from pycoingecko import CoinGeckoAPI
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import time

logger = logging.getLogger(__name__)

class CryptoService:
    def __init__(self, db: Session):
        self.db = db
        self.cg = CoinGeckoAPI()
        self.base_currency = "usd"

        
        self.timeout = 30
        self.max_retries = 3 

        # Common cryptocurrency mappings (fallback if database is empty)
        self.common_mappings = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'XRP': 'ripple',
            'SOL': 'solana',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',
            'DOGE': 'dogecoin',
            'ATOM': 'cosmos',
            'XLM': 'stellar',
            'EOS': 'eos',
            'BNB': 'binancecoin',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'DAI': 'dai',
            'UNI': 'uniswap',
            'AAVE': 'aave',
            'MKR': 'maker',
            'COMP': 'compound-governance-token',
            'YFI': 'yearn-finance',
            'SNX': 'havven',
            'CRV': 'curve-dao-token',
            'SUSHI': 'sushi',
            '1INCH': '1inch',
            'REN': 'republic-protocol',
            'BAL': 'balancer',
            'KNC': 'kyber-network',
            'ZRX': '0x'
        }
    
    # PRICES AND MARKET DATA
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price by symbol with comprehensive error handling"""
        symbol_upper = symbol.upper()
        
        for attempt in range(self.max_retries):
            try:
                coin_id = self._get_coin_id_from_symbol(symbol_upper)
                if not coin_id:
                    logger.error(f"No CoinGecko ID available for symbol: {symbol_upper}")
                    return None
                
                logger.info(f"Fetching price for {symbol_upper} (CoinGecko ID: {coin_id})")
                
                # Use CoinGecko API to get price data
                data = self.cg.get_price(
                    ids=coin_id, 
                    vs_currencies=self.base_currency, 
                    include_market_cap=True, 
                    include_24hr_vol=True,
                    include_24hr_change=True, 
                    include_last_updated_at=True
                )
                
                logger.debug(f"CoinGecko API response: {data}")
                
                if coin_id in data and data[coin_id].get(self.base_currency) is not None:
                    price_data = {
                        'symbol': symbol_upper,
                        'coin_id': coin_id,
                        'price': data[coin_id][self.base_currency],
                        'market_cap': data[coin_id].get(f'{self.base_currency}_market_cap'),
                        'volume_24h': data[coin_id].get(f'{self.base_currency}_24h_vol'),
                        'price_change_24h': data[coin_id].get(f'{self.base_currency}_24h_change'),
                        'last_updated': datetime.fromtimestamp(data[coin_id].get('last_updated_at', datetime.now().timestamp()))
                    }
                    logger.info(f"Successfully fetched price for {symbol_upper}: ${price_data['price']}")
                    return price_data
                else:
                    logger.warning(f"No price data in API response for {symbol_upper}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        return None
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {symbol_upper}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"All price fetch attempts failed for {symbol_upper}")
                    return None
        
        return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Get prices of multiple cryptocurrencies"""
        results = {}
        for symbol in symbols:
            price_data = self.get_current_price(symbol)
            if price_data:
                results[symbol.upper()] = price_data
        return results
    
    def get_detailed_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed market data"""
        try:
            coin_id = self._get_coin_id_from_symbol(symbol)
            if not coin_id:
                return None
            
            # Get complete coin data
            coin_data = self.cg.get_coin_by_id(
                id=coin_id, 
                localization=False, 
                tickers=False, 
                market_data=True, 
                community_data=False, 
                developer_data=False, 
                sparkline=False
            )
            
            if not coin_data:
                return None
            
            market_data = coin_data.get('market_data', {})
            return {
                'symbol': symbol.upper(),
                'coin_id': coin_id,
                'current_price': market_data.get('current_price', {}).get(self.base_currency),
                'market_cap': market_data.get('market_cap', {}).get(self.base_currency),
                'market_cap_rank': coin_data.get('market_cap_rank'),
                'total_volume': market_data.get('total_volume', {}).get(self.base_currency),
                'price_change_24h': market_data.get('price_change_24h', {}).get(self.base_currency),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h', {}).get(self.base_currency),
                'price_change_percentage_7d': market_data.get('price_change_percentage_7d', {}).get(self.base_currency),
                'price_change_percentage_30d': market_data.get('price_change_percentage_30d', {}).get(self.base_currency),
                'price_change_percentage_1y': market_data.get('price_change_percentage_1y', {}).get(self.base_currency),
                'ath': market_data.get('ath', {}).get(self.base_currency),
                'ath_change_percentage': market_data.get('ath_change_percentage', {}).get(self.base_currency),
                'ath_date': market_data.get('ath_date', {}).get(self.base_currency),
                'atl': market_data.get('atl', {}).get(self.base_currency),
                'atl_change_percentage': market_data.get('atl_change_percentage', {}).get(self.base_currency),
                'atl_date': market_data.get('atl_date', {}).get(self.base_currency),
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'max_supply': market_data.get('max_supply'),
                'last_updated': market_data.get('last_updated')
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed market data for {symbol}: {str(e)}")
            return None
    
    # PROJECT INFORMATION
    def get_coin_profile(self, symbol: str, language: str = 'es') -> Optional[Dict[str, Any]]:
        """Get complete profile of a cryptocurrency project"""
        try:
            coin_id = self._get_coin_id_from_symbol(symbol)
            if not coin_id:
                return None
            
            coin_data = self.cg.get_coin_by_id(
                id=coin_id, 
                localization=True, 
                tickers=True, 
                market_data=False, 
                community_data=True, 
                developer_data=True, 
                sparkline=False
            )
            
            if not coin_data:
                return None
            
            # Process description by language
            description = ""
            if language == 'es' and coin_data.get('description', {}).get('es'):
                description = coin_data['description']['es']
            else:
                description = coin_data['description']['en']
            
            return {
                'symbol': symbol.upper(),
                'coin_id': coin_id,
                'name': coin_data.get('name'),
                'description': description,
                'website': coin_data.get('links', {}).get('homepage', [None])[0],
                'whitepaper_url': coin_data.get('links', {}).get('whitepaper'),
                'github_url': coin_data.get('links', {}).get('repos_url', {}).get('github', [None])[0],
                'categories': coin_data.get('categories', []),
                'market_cap_rank': coin_data.get('market_cap_rank'),
                'logo_url': coin_data.get('image', {}).get('large'),
                'tags': coin_data.get('tags'),
                'community_data': {
                    'twitter_followers': coin_data.get('community_data', {}).get('twitter_followers'),
                    'reddit_subscribers': coin_data.get('community_data', {}).get('reddit_subscribers'),
                    'telegram_channel_user_count': coin_data.get('community_data', {}).get('telegram_channel_user_count'),
                },
                'developer_data': {
                    'forks': coin_data.get('developer_data', {}).get('forks'),
                    'stars': coin_data.get('developer_data', {}).get('stars'),
                    'subscribers': coin_data.get('developer_data', {}).get('subscribers'),
                    'total_issues': coin_data.get('developer_data', {}).get('total_issues'),
                    'closed_issues': coin_data.get('developer_data', {}).get('closed_issues'),
                    'pull_requests_merged': coin_data.get('developer_data', {}).get('pull_requests_merged'),
                },
                'links': {
                    'homepage': coin_data.get('links', {}).get('homepage', []),
                    'blockchain_site': coin_data.get('links', {}).get('blockchain_site', []),
                    'official_forum_url': coin_data.get('links', {}).get('official_forum_url', []),
                    'chat_url': coin_data.get('links', {}).get('chat_url', []),
                    'announcement_url': coin_data.get('links', {}).get('announcement_url', []),
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting coin profile for {symbol}: {str(e)}")
            return None
    
    # TECHNICAL DATA AND CHARTS
    def get_historical_data(self, symbol: str, days: int = 30, interval: str = 'daily') -> Optional[List[Dict]]:
        """Get historical price data"""
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
    
    # GLOBAL MARKET DATA
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
    
    # CACHE AND DATABASE
    def update_crypto_profiles_cache(self, symbols: List[str] = None) -> bool:
        """Update cryptocurrency profiles cache in database"""
        try:
            from app.models.crypto.crypto_models import CryptoSymbolMapping
            
            if not symbols:
                # Get symbols from database
                mappings = self.db.query(CryptoSymbolMapping).filter(
                    CryptoSymbolMapping.is_active == True
                ).all()
                symbols = [mapping.symbol for mapping in mappings]
            
            for symbol in symbols:
                profile_data = self.get_coin_profile(symbol)
                if profile_data:
                    self._save_crypto_profile(profile_data)
                
                # Small pause to avoid API rate limiting
                time.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating crypto profiles cache: {str(e)}")
            return False
    
    def _get_coin_id_from_symbol(self, symbol: str) -> Optional[str]:
        """Get CoinGecko ID from symbol with multiple fallback strategies"""
        symbol_upper = symbol.upper()
        
        try:
            # Strategy 1: Try database first
            from app.models.crypto.crypto_models import CryptoSymbolMapping
            mapping = self.db.query(CryptoSymbolMapping).filter(
                CryptoSymbolMapping.symbol == symbol_upper,
                CryptoSymbolMapping.is_active == True
            ).first()
            
            if mapping:
                logger.info(f"Found coin ID in database: {symbol_upper} -> {mapping.coingecko_id}")
                return mapping.coingecko_id
            
            # Strategy 2: Try common mappings
            if symbol_upper in self.common_mappings:
                coin_id = self.common_mappings[symbol_upper]
                logger.info(f"Found coin ID in common mappings: {symbol_upper} -> {coin_id}")
                return coin_id
            
            # Strategy 3: Try CoinGecko search as last resort
            logger.info(f"Symbol {symbol_upper} not found in mappings, trying CoinGecko search...")
            search_results = self.cg.search(symbol_upper)
            coins = search_results.get('coins', [])
            
            if coins:
                # Return the first (most relevant) result
                coin_id = coins[0]['id']
                logger.info(f"Found coin ID via search: {symbol_upper} -> {coin_id}")
                return coin_id
            else:
                logger.warning(f"No CoinGecko ID found for symbol: {symbol_upper}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting coin ID for {symbol_upper}: {str(e)}")
            # Final fallback to common mappings even if database fails
            return self.common_mappings.get(symbol_upper)
    
    def _save_crypto_profile(self, profile_data: Dict[str, Any]) -> None:
        """Save cryptocurrency profile in database"""
        try:
            from app.models.crypto.crypto_models import CryptoProfile
            
            existing_profile = self.db.query(CryptoProfile).filter(
                CryptoProfile.id == profile_data['coin_id']
            ).first()
            
            cache_until = datetime.now() + timedelta(hours=24)  # 24 hours cache
            
            if existing_profile:
                # Update existing profile
                existing_profile.symbol = profile_data['symbol']
                existing_profile.name = profile_data['name']
                existing_profile.description_es = profile_data.get('description')
                existing_profile.description_en = profile_data.get('description')
                existing_profile.website = profile_data.get('website')
                existing_profile.whitepaper_url = profile_data.get('whitepaper_url')
                existing_profile.github_url = profile_data.get('github_url')
                existing_profile.categories = profile_data.get('categories')
                existing_profile.market_cap_rank = profile_data.get('market_cap_rank')
                existing_profile.logo_url = profile_data.get('logo_url')
                existing_profile.tags = profile_data.get('tags')
                existing_profile.last_updated = datetime.now()
                existing_profile.cache_until = cache_until
            else:
                # Create new profile
                new_profile = CryptoProfile(
                    id=profile_data['coin_id'],
                    symbol=profile_data['symbol'],
                    name=profile_data['name'],
                    description_es=profile_data.get('description'),
                    description_en=profile_data.get('description'),
                    website=profile_data.get('website'),
                    whitepaper_url=profile_data.get('whitepaper_url'),
                    github_url=profile_data.get('github_url'),
                    categories=profile_data.get('categories'),
                    market_cap_rank=profile_data.get('market_cap_rank'),
                    logo_url=profile_data.get('logo_url'),
                    tags=profile_data.get('tags'),
                    last_updated=datetime.now(),
                    cache_until=cache_until
                )
                self.db.add(new_profile)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving crypto profile for {profile_data['symbol']}: {str(e)}")
            self.db.rollback()
    
    # HELPER METHODS
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
    
    def get_supported_vs_currencies(self) -> List[str]:
        """Get list of supported currencies for conversion"""
        try:
            return self.cg.get_supported_vs_currencies()
        except Exception as e:
            logger.error(f"Error getting supported currencies: {str(e)}")
            return ['usd', 'eur', 'gbp', 'jpy']