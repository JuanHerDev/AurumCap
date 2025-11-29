"""
Enhanced Fundamentals API Router
Provides real-time fundamental data from multiple sources including Yahoo Finance, FinnHub, and Alpha Vantage
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.db.database import get_db
from app.deps.auth import get_current_user
from app.models.user import User

# Initialize router
router = APIRouter(prefix="/fundamentals", tags=["fundamentals"])

# Configure logger
logger = logging.getLogger(__name__)

@router.get("/current/{symbol}")
async def get_current_fundamentals(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get enhanced current fundamental data with REAL data sources
    
    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Dictionary containing fundamental data with quality assessment
    """
    try:
        # Import service here to avoid circular imports
        from app.services.fundamentals.improved_fundamentals_service import ImprovedFundamentalsService
        fundamentals_service = ImprovedFundamentalsService(db)
        
        # Get fundamental data from service
        fundamentals_data = await fundamentals_service.get_current_fundamentals(symbol)
        
        # Handle case where no data is found
        if not fundamentals_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Real fundamental data not found for symbol: {symbol}. " +
                       "The symbol may not exist or all data sources may be unavailable."
            )
        
        # Prepare response data
        response_data = {
            "success": True,
            "data": fundamentals_data,
            "message": "Current fundamentals retrieved successfully",
            "data_quality": _assess_data_quality(fundamentals_data),
            "data_source": fundamentals_data.get('source', 'unknown'),
            "is_real_data": True
        }
        
        # Add source information for transparency
        source = fundamentals_data.get('source', '')
        if source == 'yahoo_finance':
            response_data["source_info"] = "Data from Yahoo Finance (free, no API key required)"
        elif source == 'finnhub':
            response_data["source_info"] = "Data from FinnHub API"
        elif source == 'alpha_vantage':
            response_data["source_info"] = "Data from Alpha Vantage API"
        
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and handle unexpected errors
        logger.error(f"Error getting current fundamentals for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving current fundamentals: {str(e)}"
        )

@router.get("/historical/{symbol}")
async def get_historical_fundamentals(
    symbol: str,
    period_type: str = Query("annual", regex="^(annual|quarterly)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical fundamental data with REAL data
    
    Args:
        symbol: Stock symbol
        period_type: 'annual' or 'quarterly'
        limit: Number of data points to return (1-50)
    
    Returns:
        Historical fundamental data with metadata
    """
    try:
        # Import service here to avoid circular imports
        from app.services.fundamentals.improved_fundamentals_service import ImprovedFundamentalsService
        fundamentals_service = ImprovedFundamentalsService(db)
        
        # Get historical data from service
        historical_data = await fundamentals_service.get_historical_fundamentals(
            symbol, period_type, limit
        )
        
        # Handle case where no historical data is available
        if not historical_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Historical data not available for {symbol}. This may require premium API access."
            )
        
        # Check if data contains estimated values
        is_estimated = any(item.get('is_estimated', False) for item in historical_data)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "period_type": period_type,
                "data_points": len(historical_data),
                "is_estimated": is_estimated,
                "historical_data": historical_data
            },
            "message": "Historical fundamentals retrieved successfully" + 
                      (" (estimated data)" if is_estimated else " (real data)")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical fundamentals for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving historical fundamentals: {str(e)}"
        )

@router.get("/sector/{sector}")
async def get_sector_metrics(
    sector: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get enhanced sector metrics with automatic data population
    
    Args:
        sector: Sector name (e.g., Technology, Healthcare)
    
    Returns:
        Sector metrics and aggregated data
    """
    try:
        # Import service here to avoid circular imports
        from app.services.fundamentals.improved_fundamentals_service import ImprovedFundamentalsService
        fundamentals_service = ImprovedFundamentalsService(db)
        
        # Get sector metrics from service
        sector_data = await fundamentals_service.get_sector_metrics(sector)
        
        # Handle case where sector is not found
        if not sector_data:
            # Suggest available sectors to user
            available_sectors = await _get_available_sectors(db)
            raise HTTPException(
                status_code=404, 
                detail=f"Sector '{sector}' not found. Available sectors: {', '.join(available_sectors)}"
            )
        
        return {
            "success": True,
            "data": sector_data,
            "message": "Sector metrics retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sector metrics for {sector}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving sector metrics: {str(e)}"
        )

@router.get("/calendar/economic")
async def get_economic_calendar(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    country: str = Query("US", description="Country code (US, EU, etc.)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get economic calendar events with improved date handling
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        country: Country code for filtering events
    
    Returns:
        Economic calendar events within specified date range
    """
    try:
        # Import service here to avoid circular imports
        from app.services.fundamentals.improved_fundamentals_service import ImprovedFundamentalsService
        fundamentals_service = ImprovedFundamentalsService(db)
        
        # Validate and parse dates
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Validate date range (max 3 months for performance)
        if (end_dt - start_dt).days > 90:
            raise HTTPException(
                status_code=400, 
                detail="Date range cannot exceed 90 days"
            )
        
        # Get calendar data from service
        calendar_data = await fundamentals_service.get_economic_calendar(
            start_date, end_date, country
        )
        
        return {
            "success": True,
            "data": {
                "start_date": start_date,
                "end_date": end_date,
                "country": country,
                "events_count": len(calendar_data) if calendar_data else 0,
                "events": calendar_data or []
            },
            "message": "Economic calendar retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting economic calendar: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving economic calendar: {str(e)}"
        )

@router.get("/calendar/earnings")
async def get_earnings_calendar(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    symbol: str = Query(None, description="Filter by symbol"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get earnings calendar events
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        symbol: Optional stock symbol to filter by
    
    Returns:
        Earnings calendar events
    """
    try:
        # Import service here to avoid circular imports
        from app.services.fundamentals.improved_fundamentals_service import ImprovedFundamentalsService
        fundamentals_service = ImprovedFundamentalsService(db)
        
        # Validate and parse dates
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Validate date range
        if (end_dt - start_dt).days > 90:
            raise HTTPException(
                status_code=400, 
                detail="Date range cannot exceed 90 days"
            )
        
        # Get earnings data from service
        earnings_data = await fundamentals_service.get_earnings_calendar(
            start_date, end_date, symbol
        )
        
        return {
            "success": True,
            "data": {
                "start_date": start_date,
                "end_date": end_date,
                "symbol": symbol,
                "earnings_count": len(earnings_data) if earnings_data else 0,
                "earnings": earnings_data or []
            },
            "message": "Earnings calendar retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting earnings calendar: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving earnings calendar: {str(e)}"
        )

@router.get("/calendar/upcoming")
async def get_upcoming_events(
    days: int = Query(7, ge=1, le=30, description="Number of days to look ahead"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get upcoming economic and earnings events
    
    Args:
        days: Number of days to look ahead (1-30)
    
    Returns:
        Combined economic and earnings events
    """
    try:
        # Import service here to avoid circular imports
        from app.services.fundamentals.improved_fundamentals_service import ImprovedFundamentalsService
        fundamentals_service = ImprovedFundamentalsService(db)
        
        # Calculate date range
        today = datetime.now().date()
        end_date = (today + timedelta(days=days)).isoformat()
        
        # Get both economic and earnings events
        economic_events = await fundamentals_service.get_economic_calendar(
            today.isoformat(), end_date, 'US'
        )
        
        earnings_events = await fundamentals_service.get_earnings_calendar(
            today.isoformat(), end_date, None
        )
        
        # Combine and sort events by date
        all_events = []
        if economic_events:
            all_events.extend(economic_events)
        if earnings_events:
            all_events.extend(earnings_events)
        
        # Sort events by date
        all_events.sort(key=lambda x: x.get('event_date', datetime.max))
        
        return {
            "success": True,
            "data": {
                "period_days": days,
                "total_events": len(all_events),
                "economic_events": len(economic_events) if economic_events else 0,
                "earnings_events": len(earnings_events) if earnings_events else 0,
                "events": all_events
            },
            "message": "Upcoming events retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting upcoming events: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving upcoming events: {str(e)}"
        )

@router.get("/sectors/all")
async def get_all_sectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all available sectors from database
    
    Returns:
        List of all sectors with stock data
    """
    try:
        from app.models.stocks.stock_models import StockProfile
        
        # Query distinct sectors from database
        sectors = db.query(StockProfile.sector).distinct().all()
        sector_list = [sector[0] for sector in sectors if sector[0]]
        
        return {
            "success": True,
            "data": {
                "sectors": sector_list,
                "total_sectors": len(sector_list)
            },
            "message": "Sectors list retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting sectors list: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving sectors list: {str(e)}"
        )

# Helper Functions

async def _get_available_sectors(db: Session) -> List[str]:
    """
    Get list of available sectors from database
    
    Args:
        db: Database session
    
    Returns:
        List of sector names
    """
    try:
        from app.models.stocks.stock_models import StockProfile
        sectors = db.query(StockProfile.sector).distinct().all()
        return [sector[0] for sector in sectors if sector[0]]
    except Exception:
        # Fallback sectors if database query fails
        return ["Technology", "Healthcare", "Financial Services", "Consumer Cyclical"]

def _assess_data_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess the quality and completeness of fundamental data
    
    Args:
        data: Fundamental data dictionary
    
    Returns:
        Data quality assessment with metrics
    """
    # Count non-null fields
    filled_fields = sum(1 for v in data.values() if v is not None)
    total_fields = len(data)
    
    # Calculate completeness percentage
    completeness = (filled_fields / total_fields) * 100 if total_fields > 0 else 0
    
    # Determine quality level
    if completeness > 80:
        quality = "high"
    elif completeness > 50:
        quality = "medium"
    else:
        quality = "low"
    
    return {
        "completeness_percentage": round(completeness, 2),
        "filled_fields": filled_fields,
        "total_fields": total_fields,
        "quality": quality
    }