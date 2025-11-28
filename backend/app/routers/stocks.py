from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.database import get_db
from app.deps.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("/price/{symbol}")
def get_stock_price(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current price for a stock (placeholder)"""
    # TODO: Integrar con TwelveData API
    mock_prices = {
        'AAPL': 180.0, 'TSLA': 250.0, 'MSFT': 330.0,
        'GOOGL': 140.0, 'AMZN': 150.0, 'META': 320.0
    }
    
    price = mock_prices.get(symbol.upper())
    if not price:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    return {
        "symbol": symbol.upper(),
        "price": price,
        "currency": "USD",
        "last_updated": datetime.now()
    }

@router.get("/profile/{symbol}")
def get_stock_profile(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get profile for a stock"""
    # TODO: Integrar con FinnHub API
    return {
        "symbol": symbol.upper(),
        "message": "Stock profile endpoint - integrate with FinnHub API"
    }