# routers/fundamentals_unified.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.database import get_db
from app.deps.auth import get_current_user
from app.models.user import User
from app.services.fundamentals.improved_fundamentals_service import ImprovedFundamentalsService

router = APIRouter(prefix="/fundamentals", tags=["fundamentals"])

def get_fundamentals_service(db: Session = Depends(get_db)) -> ImprovedFundamentalsService:
    """Get ImprovedFundamentalsService instance"""
    return ImprovedFundamentalsService(db)

@router.get("/current/{symbol}")
async def get_current_fundamentals(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fundamentals_service: ImprovedFundamentalsService = Depends(get_fundamentals_service)
):
    """Get enhanced current fundamental data with quality assessment"""
    try:
        fundamentals_data = await fundamentals_service.get_current_fundamentals(symbol)
        
        if not fundamentals_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Fundamental data not found for symbol: {symbol}. The symbol may not exist or API limits may be reached."
            )
        
        return {
            "success": True,
            "data": fundamentals_data,
            "message": "Current fundamentals retrieved successfully",
            "data_quality": _assess_data_quality(fundamentals_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
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
    fundamentals_service: ImprovedFundamentalsService = Depends(get_fundamentals_service)
):
    """Get historical fundamental data with fallback support"""
    try:
        historical_data = await fundamentals_service.get_historical_fundamentals(
            symbol, period_type, limit
        )
        
        if not historical_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Historical data not available for {symbol}. This may require premium API access."
            )
        
        # Check if data is estimated
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
                      (" (estimated data)" if is_estimated else "")
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
    fundamentals_service: ImprovedFundamentalsService = Depends(get_fundamentals_service)
):
    """Get enhanced sector metrics with automatic data population"""
    try:
        sector_data = await fundamentals_service.get_sector_metrics(sector)
        
        if not sector_data:
            # Suggest available sectors
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
    fundamentals_service: ImprovedFundamentalsService = Depends(get_fundamentals_service)
):
    """Get economic calendar events with improved date handling"""
    try:
        # Validate date range (max 3 months)
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        if (end_dt - start_dt).days > 90:
            raise HTTPException(
                status_code=400, 
                detail="Date range cannot exceed 90 days"
            )
        
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
    fundamentals_service: ImprovedFundamentalsService = Depends(get_fundamentals_service)
):
    """Get earnings calendar events"""
    try:
        # Validate date range (max 3 months)
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        if (end_dt - start_dt).days > 90:
            raise HTTPException(
                status_code=400, 
                detail="Date range cannot exceed 90 days"
            )
        
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
    fundamentals_service: ImprovedFundamentalsService = Depends(get_fundamentals_service)
):
    """Get upcoming economic and earnings events"""
    try:
        today = datetime.now().date()
        end_date = (today + timedelta(days=days)).isoformat()
        
        # Get both economic and earnings events
        economic_events = await fundamentals_service.get_economic_calendar(
            today.isoformat(), end_date, 'US'
        )
        
        earnings_events = await fundamentals_service.get_earnings_calendar(
            today.isoformat(), end_date, None
        )
        
        # Combine and sort events
        all_events = []
        if economic_events:
            all_events.extend(economic_events)
        if earnings_events:
            all_events.extend(earnings_events)
        
        # Sort by date
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
    """Get list of all available sectors"""
    try:
        from app.models.stocks.stock_models import StockProfile
        
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

# Helper functions
async def _get_available_sectors(db: Session) -> List[str]:
    """Get list of available sectors"""
    try:
        from app.models.stocks.stock_models import StockProfile
        sectors = db.query(StockProfile.sector).distinct().all()
        return [sector[0] for sector in sectors if sector[0]]
    except:
        return ["Technology", "Healthcare", "Financial Services", "Consumer Cyclical"]

def _assess_data_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the quality of fundamental data"""
    filled_fields = sum(1 for v in data.values() if v is not None)
    total_fields = len(data)
    completeness = (filled_fields / total_fields) * 100
    
    return {
        "completeness_percentage": round(completeness, 2),
        "filled_fields": filled_fields,
        "total_fields": total_fields,
        "quality": "high" if completeness > 80 else "medium" if completeness > 50 else "low"
    }

# Add logging
import logging
logger = logging.getLogger(__name__)