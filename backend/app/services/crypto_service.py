# services/crypto_service.py
import os
import requests
import asyncio
import time
from typing import Optional, Dict, Any, List, Union
from decimal import Decimal, ROUND_HALF_UP
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
TIMEOUT = 10
CACHE_TTL_PRICES = 60  # 1 minute
CACHE_TTL_DETAILS = 300  # 5 minutes
CACHE_TTL_PROFILES = 86400  # 24 hours for profiles

@dataclass
class CryptoProfileData:
    id: str
    symbol: str
    name: str
    description_es: str
    description_en: str
    website: str
    whitepaper_url: str
    github_url: str
    categories: List[str]
    market_cap_rank: int
    logo_url: str
    tags: List[str]
    last_updated: datetime

@dataclass
class CryptoPriceData:
    symbol: str
    current_price: Decimal
    price_change_24h: Decimal
    price_change_percentage_24h: Decimal
    market_cap: Decimal
    volume_24h: Decimal
    circulating_supply: Decimal
    total_supply: Decimal
    max_supply: Decimal
    ath: Decimal
    ath_change_percentage: Decimal
    atl: Decimal
    atl_change_percentage: Decimal
    high_24h: Decimal
    low_24h: Decimal
    last_updated: datetime

@dataclass
class CryptoMarketData:
    symbol: str
    price: Decimal
    change_24h: Decimal
    change_percentage_24h: Decimal
    market_cap: Decimal
    volume_24h: Decimal
    sparkline_7d: List[Decimal]

class CoinGeckoService:
    def __init__(self):
        self._cache = {}
        self._session = None
        self._symbol_to_id_map = {}
        self._last_request_time = 0
        self._min_interval = 0.5  # 2 requests per second
        
    async def __aenter__(self):
        self._session = requests.Session()
        await self._preload_symbol_mapping()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            self._session.close()
            
    async def _rate_limit(self):
        """Respetar límites de la API free"""
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_interval:
            await asyncio.sleep(self._min_interval - time_since_last)
        self._last_request_time = time.time()
        
    async def _preload_symbol_mapping(self):
        """Precargar mapeo de símbolos a IDs"""
        try:
            await self._rate_limit()
            response = self._session.get(
                f"{COINGECKO_API}/coins/list",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            
            for coin in response.json():
                symbol = coin['symbol'].lower()
                self._symbol_to_id_map[symbol] = coin['id']
                
            logger.info(f"Loaded {len(self._symbol_to_id_map)} crypto symbol mappings")
        except Exception as e:
            logger.warning(f"Failed to preload symbol mapping: {e}")

    def _get_coin_id(self, symbol: str) -> Optional[str]:
        return self._symbol_to_id_map.get(symbol.lower())

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value)).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
        except:
            return None

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Request genérico con rate limiting"""
        if params is None:
            params = {}
            
        await self._rate_limit()
        
        try:
            response = self._session.get(
                f"{COINGECKO_API}/{endpoint}",
                params=params,
                timeout=TIMEOUT
            )
            
            if response.status_code == 429:
                logger.warning("Rate limit hit, waiting 60 seconds...")
                await asyncio.sleep(60)
                return await self._make_request(endpoint, params)
                
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None

    # ==================== PROFILE METHODS ====================
    
    async def get_crypto_profile(self, symbol: str) -> Optional[CryptoProfileData]:
        """Obtener perfil completo para poblar crypto_profiles"""
        coin_id = self._get_coin_id(symbol) or await self._find_coin_id(symbol)
        if not coin_id:
            return None

        params = {
            "localization": "es,en",
            "tickers": "false",
            "market_data": "false",
            "community_data": "true",
            "developer_data": "true",
            "sparkline": "false"
        }

        data = await self._make_request(f"coins/{coin_id}", params)
        if not data:
            return None

        # Procesar descripciones
        description = data.get('description', {})
        description_es = description.get('es', '').strip() or description.get('en', '')
        description_en = description.get('en', '')

        # Procesar links
        links = data.get('links', {})
        website = links.get('homepage', [''])[0] if links.get('homepage') else ''
        whitepaper = links.get('whitepaper', '') or (links.get('whitepaper', [''])[0] if links.get('whitepaper') else '')
        
        # Buscar GitHub en repositorios
        github_url = ''
        for repo in links.get('repos_url', {}).get('github', []):
            if 'github.com' in repo:
                github_url = repo
                break

        return CryptoProfileData(
            id=data['id'],
            symbol=data['symbol'].upper(),
            name=data['name'],
            description_es=description_es[:5000] if description_es else None,  # Truncar si es muy largo
            description_en=description_en[:5000] if description_en else None,
            website=website[:500] if website else None,
            whitepaper_url=whitepaper[:500] if whitepaper else None,
            github_url=github_url[:500] if github_url else None,
            categories=data.get('categories', []),
            market_cap_rank=data.get('market_cap_rank'),
            logo_url=data.get('image', {}).get('large', ''),
            tags=[tag for tag in data.get('tags', []) if not isinstance(tag, dict)],
            last_updated=datetime.now()
        )

    async def get_crypto_profiles_batch(self, symbols: List[str]) -> Dict[str, CryptoProfileData]:
        """Obtener múltiples perfiles"""
        results = {}
        for symbol in symbols:
            profile = await self.get_crypto_profile(symbol)
            if profile:
                results[symbol] = profile
            await asyncio.sleep(0.2)  # Rate limiting entre requests
        return results

    # ==================== PRICE METHODS ====================
    
    async def get_crypto_price_data(self, symbol: str, vs_currency: str = "usd") -> Optional[CryptoPriceData]:
        """Obtener datos de precio completos"""
        coin_id = self._get_coin_id(symbol) or await self._find_coin_id(symbol)
        if not coin_id:
            return None

        params = {
            "ids": coin_id,
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }

        data = await self._make_request("simple/price", params)
        if not data or coin_id not in data:
            return None

        # Obtener datos detallados para supply y ATH/ATL
        detail_params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        
        detail_data = await self._make_request(f"coins/{coin_id}", detail_params)
        market_data = detail_data.get('market_data', {}) if detail_data else {}

        coin_data = data[coin_id]
        return CryptoPriceData(
            symbol=symbol.upper(),
            current_price=self._to_decimal(coin_data.get(vs_currency)),
            price_change_24h=self._to_decimal(coin_data.get(f"{vs_currency}_24h_change")),
            price_change_percentage_24h=self._to_decimal(coin_data.get(f"{vs_currency}_24h_change")),
            market_cap=self._to_decimal(coin_data.get(f"{vs_currency}_market_cap")),
            volume_24h=self._to_decimal(coin_data.get(f"{vs_currency}_24h_vol")),
            circulating_supply=self._to_decimal(market_data.get('circulating_supply')),
            total_supply=self._to_decimal(market_data.get('total_supply')),
            max_supply=self._to_decimal(market_data.get('max_supply')),
            ath=self._to_decimal(market_data.get('ath', {}).get(vs_currency)),
            ath_change_percentage=self._to_decimal(market_data.get('ath_change_percentage', {}).get(vs_currency)),
            atl=self._to_decimal(market_data.get('atl', {}).get(vs_currency)),
            atl_change_percentage=self._to_decimal(market_data.get('atl_change_percentage', {}).get(vs_currency)),
            high_24h=self._to_decimal(market_data.get('high_24h', {}).get(vs_currency)),
            low_24h=self._to_decimal(market_data.get('low_24h', {}).get(vs_currency)),
            last_updated=datetime.now()
        )

    async def get_crypto_prices_batch(self, symbols: List[str], vs_currency: str = "usd") -> Dict[str, CryptoMarketData]:
        """Obtener precios para múltiples cryptos (optimizado)"""
        coin_ids = []
        symbol_to_id = {}
        
        for symbol in symbols:
            coin_id = self._get_coin_id(symbol) or await self._find_coin_id(symbol)
            if coin_id:
                coin_ids.append(coin_id)
                symbol_to_id[coin_id] = symbol

        if not coin_ids:
            return {}

        params = {
            "vs_currency": vs_currency,
            "ids": ",".join(coin_ids),
            "order": "market_cap_desc",
            "per_page": 250,  # Máximo permitido
            "page": 1,
            "sparkline": "true",
            "price_change_percentage": "24h"
        }

        data = await self._make_request("coins/markets", params)
        if not data:
            return {}

        results = {}
        for coin_data in data:
            coin_id = coin_data.get('id')
            symbol = symbol_to_id.get(coin_id)
            if symbol:
                results[symbol] = CryptoMarketData(
                    symbol=symbol,
                    price=self._to_decimal(coin_data.get('current_price')),
                    change_24h=self._to_decimal(coin_data.get('price_change_24h')),
                    change_percentage_24h=self._to_decimal(coin_data.get('price_change_percentage_24h')),
                    market_cap=self._to_decimal(coin_data.get('market_cap')),
                    volume_24h=self._to_decimal(coin_data.get('total_volume')),
                    sparkline_7d=[self._to_decimal(price) for price in coin_data.get('sparkline_in_7d', {}).get('price', [])]
                )

        return results

    # ==================== HISTORICAL DATA ====================
    
    async def get_historical_data(self, symbol: str, days: int = 30, vs_currency: str = "usd") -> Optional[List[Dict]]:
        """Obtener datos históricos para gráficas"""
        coin_id = self._get_coin_id(symbol) or await self._find_coin_id(symbol)
        if not coin_id:
            return None

        params = {
            "vs_currency": vs_currency,
            "days": days,
            "interval": "daily" if days > 1 else "hourly"
        }

        data = await self._make_request(f"coins/{coin_id}/market_chart", params)
        if not data:
            return None

        prices = data.get('prices', [])
        return [
            {
                'timestamp': datetime.fromtimestamp(price[0] / 1000),
                'price': self._to_decimal(price[1])
            }
            for price in prices
        ]

    # ==================== CATEGORIES ====================
    
    async def get_crypto_categories(self) -> List[Dict]:
        """Obtener todas las categorías de criptomonedas"""
        data = await self._make_request("coins/categories/list", {})
        if not data:
            return []

        categories = []
        for category in data:
            categories.append({
                'category_id': category.get('category_id'),
                'name': category.get('name'),
            })
            
        return categories

    # ==================== HELPER METHODS ====================
    
    async def _find_coin_id(self, symbol: str) -> Optional[str]:
        """
        Search id by symbol prioritizing principal coins.
        """

        # First verify global mapping
        if symbol.lower() in self._symbol_to_id_map:
            return self._symbol_to_id_map[symbol.lower()]
        
        params = {"query": symbol}
        data = await self._make_request("search", params)

        if not data or 'coins' not in data:
            return None
        
        coins = data['coins']

        priority_mapping = {
        'btc': 'bitcoin',
        'eth': 'ethereum',
        'ada': 'cardano', 
        'dot': 'polkadot',
        'sol': 'solana',
        'matic': 'polygon',
        'avax': 'avalanche-2',
        'link': 'chainlink',
        'uni': 'uniswap',
        'aave': 'aave',
        'xrp': 'ripple',
        'doge': 'dogecoin',
        'ltc': 'litecoin',
        'bch': 'bitcoin-cash',
        'xlm': 'stellar',
        'atom': 'cosmos',
        'etc': 'ethereum-classic'
        }

        # First: Search in priority mapping
        if symbol.lower() in priority_mapping:
            coin_id = priority_mapping[symbol.lower()]
            self._symbol_to_id_map[symbol.lower()] = coin_id
            logger.info(f"Found {symbol} via priority mapping: {coin_id}")
            return coin_id
        
        # Second: Search in results with filter by market cap
        valid_coins = []
        for coin in coins:
            coin_symbol = coin.get('symbol', '').lower()
            coin_id = coin.get('id')
            market_cap_rank = coin.get('market_cap_rank')
            name = coin.get('name', '').lower()

            # Exact match
            if coin_symbol == symbol.lower():
                # Filter by market cap rank (prioritize top 500)
                if market_cap_rank and market_cap_rank <= 500:
                    valid_coins.append({
                    'coin': coin,
                    'rank': market_cap_rank,
                    'is_exact_match': True
                    })
                elif market_cap_rank:
                    valid_coins.append({
                    'coin': coin,
                    'rank': market_cap_rank, 
                    'is_exact_match': True
                    })

            valid_coins.sort(key=lambda x: x['rank'] if x['rank'] else 9999)

            if valid_coins:
                best_coin = valid_coins[0]['coin']
                coin_id = best_coin.get('id')
                self._symbol_to_id_map[symbol.lower()] = coin_id
                logger.info(f"✅ Found {symbol} via search: {coin_id} (rank: {best_coin.get('market_cap_rank')})")
                return coin_id
            
            logger.warning(f"❌ No valid coin found for symbol: {symbol}")
            return None

# Instancia global
_crypto_service = CoinGeckoService()

# API pública
async def get_crypto_profile(symbol: str) -> Optional[CryptoProfileData]:
    async with _crypto_service as service:
        return await service.get_crypto_profile(symbol)

async def get_crypto_price_data(symbol: str, vs_currency: str = "usd") -> Optional[CryptoPriceData]:
    async with _crypto_service as service:
        return await service.get_crypto_price_data(symbol, vs_currency)

async def get_crypto_prices_batch(symbols: List[str], vs_currency: str = "usd") -> Dict[str, CryptoMarketData]:
    async with _crypto_service as service:
        return await service.get_crypto_prices_batch(symbols, vs_currency)

async def get_crypto_historical_data(symbol: str, days: int = 30, vs_currency: str = "usd") -> Optional[List[Dict]]:
    async with _crypto_service as service:
        return await service.get_historical_data(symbol, days, vs_currency)

async def get_crypto_categories() -> List[Dict]:
    async with _crypto_service as service:
        return await service.get_crypto_categories()