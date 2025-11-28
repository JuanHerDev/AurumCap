import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CryptoRealTimeService:
    def __init__(self, crypto_service: 'CryptoService'):
        self.crypto_service = crypto_service
        self.base_url = "https://api.coingecko.com/api/v3"
    
    async def get_multiple_prices_async(self, symbols: List[str]) -> Dict[str, Any]:
        """Get prices of multiple cryptos asynchronously"""
        try:
            # Get coin IDs
            coin_ids = []
            symbol_to_coin_id = {}
            
            for symbol in symbols:
                coin_id = self.crypto_service._get_coin_id_from_symbol(symbol)
                if coin_id:
                    coin_ids.append(coin_id)
                    symbol_to_coin_id[coin_id] = symbol
            
            if not coin_ids:
                return {}
            
            # Make async request
            async with aiohttp.ClientSession() as session:
                coin_ids_param = ','.join(coin_ids)
                url = f"{self.base_url}/simple/price"
                params = {
                    'ids': coin_ids_param,
                    'vs_currencies': self.crypto_service.base_currency,
                    'include_market_cap': 'true',
                    'include_24hr_vol': 'true',
                    'include_24hr_change': 'true',
                    'include_last_updated_at': 'true'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = {}
                        
                        for coin_id, price_data in data.items():
                            symbol = symbol_to_coin_id.get(coin_id)
                            if symbol and price_data:
                                results[symbol] = {
                                    'symbol': symbol,
                                    'coin_id': coin_id,
                                    'price': price_data.get(self.crypto_service.base_currency),
                                    'market_cap': price_data.get(f'{self.crypto_service.base_currency}_market_cap'),
                                    'volume_24h': price_data.get(f'{self.crypto_service.base_currency}_24h_vol'),
                                    'price_change_24h': price_data.get(f'{self.crypto_service.base_currency}_24h_change'),
                                    'last_updated': datetime.fromtimestamp(price_data.get('last_updated_at'))
                                }
                        
                        return results
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error in async price fetch: {str(e)}")
            return {}
    
    async def get_portfolio_prices(self, portfolio_symbols: List[str]) -> Dict[str, Any]:
        """Get prices for all symbols in a portfolio efficiently"""
        return await self.get_multiple_prices_async(portfolio_symbols)