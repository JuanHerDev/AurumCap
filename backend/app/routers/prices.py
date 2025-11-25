# routers/prices.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict
from app.services.prices_crypto import get_crypto_price
from app.services.prices_stocks import get_stock_price
from decimal import Decimal

router = APIRouter(prefix="/prices", tags=["prices"])

@router.get("/all")
async def get_all_prices(
    symbols: str = Query(..., description="Comma-separated list of symbols")
):
    """Get prices for both crypto and stocks through backend"""
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    
    prices = {}
    
    for symbol in symbol_list:
        try:
            # Primero intentar como crypto
            crypto_price = await get_crypto_price(symbol)
            if crypto_price:
                prices[symbol] = str(crypto_price)
                continue
                
            # Si no es crypto, intentar como stock
            stock_price = get_stock_price(symbol)
            if stock_price:
                prices[symbol] = str(stock_price)
            else:
                prices[symbol] = None
                
        except Exception as e:
            prices[symbol] = None
    
    return prices