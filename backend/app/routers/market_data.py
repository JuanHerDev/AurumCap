from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from app.services import (
    get_crypto_profile,
    get_crypto_price_data, 
    get_stock_profile,
    get_stock_fundamentals,
    get_economic_calendar
)
from app.services.crypto_service import CoinGeckoService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market-data"])

@router.get("/crypto/{symbol}/profile")
async def get_crypto_profile_endpoint(symbol: str):
    """Get complete crypto profile"""
    try:
        profile = await get_crypto_profile(symbol)
        if not profile:
            raise HTTPException(404, "Crypto symbol not found")
        return profile
    except Exception as e:
        raise HTTPException(500, f"Error fetching crypto profile: {str(e)}")

@router.get("/stocks/{symbol}/fundamentals")  
async def get_stock_fundamentals_endpoint(symbol: str):
    """Get complete stock fundamentals - CON VALIDACIÓN"""
    try:
        # Validate symbol is correct
        if len(symbol) > 5 or not symbol.isalpha():
            raise HTTPException(400, f"{symbol} no parece ser un símbolo de stock válido")
            
        # Verify not a crypto symbol (simple check)
        crypto_symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'MATIC', 'AVAX', 'LINK', 'UNI', 'AAVE']
        if symbol.upper() in crypto_symbols:
            raise HTTPException(400, f"{symbol} es una criptomoneda. Use /market/crypto/{symbol}/profile")
            
        fundamentals = await get_stock_fundamentals(symbol)
        if not fundamentals:
            raise HTTPException(404, f"No se encontraron fundamentales para {symbol}")
        return fundamentals
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error fetching stock fundamentals: {str(e)}")
    
@router.get("/economic-calendar")
async def get_economic_calendar_endpoint(
    days: int = Query(30, ge=1, le=90)
):
    """Get economic calendar"""
    try:
        events = await get_economic_calendar()
        return events
    except Exception as e:
        raise HTTPException(500, f"Error fetching economic calendar: {str(e)}")
    
@router.get("/search/{query}")
async def search_symbols(query: str):
    """Buscar símbolos en todas las categorías - VERSION MEJORADA"""
    results = {
        "crypto": [],
        "stocks": []
    }
    
    try:
        # Buscar en crypto
        crypto_service = CoinGeckoService()
        async with crypto_service as service:
            search_data = await service._make_request("search", {"query": query})
            if search_data and 'coins' in search_data:
                for coin in search_data['coins'][:10]:  # Más resultados
                    # Filtrar resultados de baja calidad
                    market_cap_rank = coin.get('market_cap_rank')
                    if market_cap_rank and market_cap_rank <= 1000:  # Solo top 1000
                        results["crypto"].append({
                            "symbol": coin.get('symbol', '').upper(),
                            "name": coin.get('name'),
                            "market_cap_rank": market_cap_rank,
                            "id": coin.get('id'),  # Para usar en requests
                            "type": "crypto",
                            "thumb": coin.get('thumb')  # Imagen pequeña
                        })
    
    except Exception as e:
        logger.error(f"Error searching crypto symbols: {e}")
    
    # Ordenar crypto por market cap rank
    results["crypto"].sort(key=lambda x: x["market_cap_rank"] if x["market_cap_rank"] else 9999)
    
    return results
