from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.database import get_db
from app.deps.auth import get_current_user
from app.services.crypto import CryptoServiceFactory
from app.models.user import User

router = APIRouter(prefix="/crypto", tags=["crypto"])

@router.get("/price/{symbol}")
def get_crypto_price(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current price for a cryptocurrency"""
    crypto_service = CryptoServiceFactory.create_crypto_service(db)
    
    price_data = crypto_service.get_current_price(symbol)
    if not price_data:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    
    return price_data

@router.get("/profile/{symbol}")
def get_crypto_profile(
    symbol: str,
    language: str = Query("es", regex="^(es|en)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed profile for a cryptocurrency"""
    crypto_service = CryptoServiceFactory.create_crypto_service(db)
    
    profile = crypto_service.get_coin_profile(symbol, language)
    if not profile:
        raise HTTPException(status_code=404, detail="Cryptocurrency profile not found")
    
    return profile

@router.get("/market-data/{symbol}")
def get_crypto_market_data(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed market data for a cryptocurrency"""
    crypto_service = CryptoServiceFactory.create_crypto_service(db)
    
    market_data = crypto_service.get_detailed_market_data(symbol)
    if not market_data:
        raise HTTPException(status_code=404, detail="Cryptocurrency market data not found")
    
    return market_data

@router.get("/historical/{symbol}")
def get_crypto_historical_data(
    symbol: str,
    days: int = Query(30, ge=1, le=365),
    interval: str = Query("daily", regex="^(daily|hourly)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get historical price data for a cryptocurrency"""
    crypto_service = CryptoServiceFactory.create_crypto_service(db)
    
    historical_data = crypto_service.get_historical_data(symbol, days, interval)
    if not historical_data:
        raise HTTPException(status_code=404, detail="Historical data not found")
    
    return historical_data

@router.get("/global/market")
def get_global_crypto_market(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get global cryptocurrency market data"""
    crypto_service = CryptoServiceFactory.create_crypto_service(db)
    
    global_data = crypto_service.get_global_market_data()
    if not global_data:
        raise HTTPException(status_code=404, detail="Global market data not available")
    
    return global_data

@router.get("/search")
def search_cryptocurrencies(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for cryptocurrencies by name or symbol"""
    crypto_service = CryptoServiceFactory.create_crypto_service(db)
    
    results = crypto_service.search_coins(query)
    return {"query": query, "results": results}

@router.get("/trending")
def get_trending_cryptocurrencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trending cryptocurrencies"""
    crypto_service = CryptoServiceFactory.create_crypto_service(db)
    
    trending = crypto_service.get_trending_coins()
    return {"trending": trending}