# routers/stocks.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.database import get_db
from app.deps.auth import get_current_user
from app.models.user import User
from app.services.stocks.factory import StockServiceFactory
from app.services.stocks.real_time_service import StockRealTimeService
from app.services.stocks.stock_service import StockService

router = APIRouter(prefix="/stocks", tags=["stocks"])

# Global instance for real-time service
_stock_real_time_service = None

def get_stock_service(db: Session = Depends(get_db)) -> Any:
    """Get StockService instance"""
    return StockServiceFactory.create_stock_service(db)

def get_real_time_service(stock_service: Any = Depends(get_stock_service)) -> StockRealTimeService:
    """Get StockRealTimeService instance"""
    global _stock_real_time_service
    if _stock_real_time_service is None:
        _stock_real_time_service = StockServiceFactory.create_real_time_service(stock_service)
        # Start background updates
        import asyncio
        asyncio.create_task(_stock_real_time_service.start_price_updates(interval_seconds=30))
    return _stock_real_time_service

@router.get("/price/{symbol}")
async def get_stock_price(
    symbol: str,
    exchange: str = Query(None, description="Stock exchange (NYSE, NASDAQ, etc.)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: Any = Depends(get_stock_service)
):
    """Get current price for a stock using TwelveData API"""
    try:
        price_data = await stock_service.get_current_price(symbol, exchange)
        
        if not price_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Stock price not found for symbol: {symbol}"
            )
        
        return {
            "success": True,
            "data": price_data,
            "message": "Price retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock price for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving stock price: {str(e)}"
        )

@router.get("/profile/{symbol}")
async def get_stock_profile(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: Any = Depends(get_stock_service)
):
    """Get comprehensive stock profile using FinnHub API with caching"""
    try:
        profile_data = await stock_service.get_stock_profile(symbol)
        
        if not profile_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Stock profile not found for symbol: {symbol}"
            )
        
        return {
            "success": True,
            "data": profile_data,
            "message": "Profile retrieved successfully",
            "source": profile_data.get('source', 'api')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock profile for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving stock profile: {str(e)}"
        )

@router.get("/quote/{symbol}")
async def get_real_time_quote(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: Any = Depends(get_stock_service)
):
    """Get real-time stock quote with detailed information using FinnHub"""
    try:
        quote_data = await stock_service.get_real_time_quote(symbol)
        
        if not quote_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Real-time quote not available for symbol: {symbol}"
            )
        
        return {
            "success": True,
            "data": quote_data,
            "message": "Real-time quote retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting real-time quote for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving real-time quote: {str(e)}"
        )

@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    interval: str = Query("1day", regex="^(1min|5min|15min|30min|45min|1h|2h|4h|1day|1week|1month)$"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: Any = Depends(get_stock_service)
):
    """Get historical stock data using TwelveData API"""
    try:
        historical_data = await stock_service.get_historical_data(
            symbol, interval, start_date, end_date
        )
        
        if not historical_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Historical data not found for symbol: {symbol}"
            )
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "interval": interval,
                "data_points": len(historical_data),
                "historical_data": historical_data
            },
            "message": "Historical data retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical data for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving historical data: {str(e)}"
        )

@router.get("/fundamentals/{symbol}")
async def get_fundamental_data(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: Any = Depends(get_stock_service)
):
    """Get fundamental data for a stock (metrics, earnings, dividends)"""
    try:
        fundamental_data = await stock_service.get_fundamental_data(symbol)
        
        if not fundamental_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Fundamental data not found for symbol: {symbol}"
            )
        
        return {
            "success": True,
            "data": fundamental_data,
            "message": "Fundamental data retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fundamental data for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving fundamental data: {str(e)}"
        )

@router.get("/search")
async def search_stocks(
    query: str = Query(..., min_length=2, description="Company name or symbol to search"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: Any = Depends(get_stock_service)
):
    """Search for stocks by company name or symbol using FinnHub API"""
    try:
        search_results = await stock_service.search_stocks(query)
        
        return {
            "success": True,
            "data": {
                "query": query,
                "results_count": len(search_results),
                "results": search_results
            },
            "message": f"Found {len(search_results)} results for '{query}'"
        }
        
    except Exception as e:
        logger.error(f"Error searching stocks for '{query}': {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching stocks: {str(e)}"
        )

@router.get("/market/status")
async def get_market_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: Any = Depends(get_stock_service)
):
    """Get current market status and major indices"""
    try:
        market_status = await stock_service.get_market_status()
        
        return {
            "success": True,
            "data": market_status,
            "message": "Market status retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting market status: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving market status: {str(e)}"
        )

@router.get("/prices/batch")
async def get_multiple_prices(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: Any = Depends(get_stock_service)
):
    """Get prices for multiple stocks efficiently"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        if len(symbol_list) > 20:
            raise HTTPException(
                status_code=400, 
                detail="Maximum 20 symbols allowed per request"
            )
        
        prices_data = await stock_service.get_multiple_prices(symbol_list)
        
        return {
            "success": True,
            "data": {
                "requested_symbols": symbol_list,
                "found_prices": len(prices_data),
                "prices": prices_data
            },
            "message": f"Retrieved prices for {len(prices_data)} out of {len(symbol_list)} symbols"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting multiple prices for {symbols}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving multiple prices: {str(e)}"
        )

# Real-time endpoints (if using WebSockets/SSE)
@router.get("/stream/subscribe")
async def subscribe_to_stock_updates(
    symbols: str = Query(..., description="Comma-separated list of symbols to subscribe"),
    real_time_service: StockRealTimeService = Depends(get_real_time_service)
):
    """Subscribe to real-time stock updates (WebSocket/SSE)"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        # This would typically handle WebSocket connection
        # For now, return subscription confirmation
        return {
            "success": True,
            "data": {
                "subscribed_symbols": symbol_list,
                "message": "Real-time updates subscribed (WebSocket implementation required)"
            }
        }
        
    except Exception as e:
        logger.error(f"Error subscribing to stock updates: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error subscribing to updates: {str(e)}"
        )

@router.post("/cache/refresh/{symbol}")
async def refresh_stock_cache(
    symbol: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stock_service: StockService = Depends(get_stock_service)
):
    """Force refresh cache for a stock (admin/background task)"""
    try:
        # Force refresh by calling the fetch method directly
        async def refresh_profile():
            # Clear cache first
            cache_key = f"profile_{symbol.upper()}"
            if cache_key in stock_service._profile_cache:
                del stock_service._profile_cache[cache_key]
            
            # Get fresh data
            await stock_service.get_stock_profile(symbol)
        
        background_tasks.add_task(refresh_profile)
        
        return {
            "success": True,
            "message": f"Cache refresh initiated for {symbol}",
            "symbol": symbol.upper()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing cache for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error refreshing cache: {str(e)}"
        )

@router.get("/exchanges")
async def get_supported_exchanges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of supported stock exchanges"""
    try:
        from app.models.stocks.stock_models import StockExchange
        
        exchanges = db.query(StockExchange).all()
        
        exchange_list = []
        for exchange in exchanges:
            exchange_list.append({
                "exchange_code": exchange.exchange_code,
                "exchange_name": exchange.exchange_name,
                "country": exchange.country,
                "currency": exchange.currency,
                "opening_time": exchange.opening_time.isoformat() if exchange.opening_time else None,
                "closing_time": exchange.closing_time.isoformat() if exchange.closing_time else None,
                "timezone": exchange.timezone
            })
        
        return {
            "success": True,
            "data": {
                "exchanges": exchange_list,
                "total_exchanges": len(exchange_list)
            },
            "message": "Supported exchanges retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting supported exchanges: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving exchanges: {str(e)}"
        )

@router.get("/sectors")
async def get_stock_sectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of stock sectors and industries"""
    try:
        from app.models.stocks.stock_models import StockSector, StockIndustry
        
        sectors = db.query(StockSector).all()
        
        sector_list = []
        for sector in sectors:
            industries = db.query(StockIndustry).filter(
                StockIndustry.sector_id == sector.sector_id
            ).all()
            
            industry_list = []
            for industry in industries:
                industry_list.append({
                    "industry_id": industry.industry_id,
                    "industry_name": industry.industry_name,
                    "description": industry.description
                })
            
            sector_list.append({
                "sector_id": sector.sector_id,
                "sector_name": sector.sector_name,
                "description": sector.description,
                "typical_pe_ratio": sector.typical_pe_ratio,
                "typical_dividend_yield": sector.typical_dividend_yield,
                "typical_roe": sector.typical_roe,
                "industries": industry_list
            })
        
        return {
            "success": True,
            "data": {
                "sectors": sector_list,
                "total_sectors": len(sector_list)
            },
            "message": "Sectors and industries retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting sectors: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving sectors: {str(e)}"
        )

# Add logging
import logging
logger = logging.getLogger(__name__)