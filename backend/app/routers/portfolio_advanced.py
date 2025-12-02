from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.db.database import get_db
from app.deps.auth import get_current_user
from app.models.user import User
from app.schemas.risk_profile import (
    RiskProfileCreate, RiskProfileUpdate, RiskProfileOut, RiskProfileType
)
from app.schemas.investment_goal import (
    InvestmentGoalCreate, InvestmentGoalUpdate, InvestmentGoalOut
)
from app.schemas.dividend import DividendCreate, DividendUpdate, DividendOut
from app.schemas.price_alert import (
    PriceAlertCreate, PriceAlertUpdate, PriceAlertOut, AlertType, TriggerDirection
)
from app.services.portfolio_advanced import PortfolioAdvancedService
from app.models.risk_profile import RiskProfile
from app.models.investment_goal import InvestmentGoal
from app.models.dividend import Dividend
from app.models.price_alert import PriceAlert

from app.services.portfolio_advanced import PortfolioAdvancedService

router = APIRouter(prefix="/portfolio/advanced", tags=["portfolio-advanced"])

# RISK PROFILE ENDPOINTS
@router.post("/risk-profile", response_model=RiskProfileOut, status_code=status.HTTP_201_CREATED)
def create_risk_profile(
    profile_data: RiskProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update user risk profile"""
    service = PortfolioAdvancedService(db)
    
    try:
        profile = service.create_or_update_risk_profile(
            user_id=current_user.id,
            profile_type=profile_data.profile_type
        )
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating risk profile: {str(e)}"
        )

@router.get("/risk-profile", response_model=RiskProfileOut)
def get_risk_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's risk profile"""
    from app.models.risk_profile import RiskProfile
    
    profile = db.query(RiskProfile).filter(
        RiskProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk profile not found. Please create one first."
        )
    
    return profile

@router.put("/risk-profile", response_model=RiskProfileOut)
def update_risk_profile(
    profile_data: RiskProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's risk profile"""
    from app.models.risk_profile import RiskProfile
    
    profile = db.query(RiskProfile).filter(
        RiskProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk profile not found"
        )
    
    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.now()
    db.commit()
    db.refresh(profile)
    
    return profile

@router.get("/allocation/current")
def get_current_allocation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current portfolio allocation"""
    service = PortfolioAdvancedService(db)
    
    try:
        allocation = service.calculate_portfolio_allocation(current_user.id)
        return {
            "user_id": current_user.id,
            "allocation": allocation,
            "calculated_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating allocation: {str(e)}"
        )

@router.get("/rebalancing/recommendations")
def get_rebalancing_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio rebalancing recommendations"""
    service = PortfolioAdvancedService(db)
    
    try:
        recommendations = service.get_rebalancing_recommendations(current_user.id)
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )

# SELL CALCULATOR ENDPOINTS
@router.post("/sell-calculator/profits-only")
def calculate_sell_profits_only(
    investment_id: int = Query(..., gt=0),
    target_amount: float = Query(..., gt=0),
    current_price: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate how much to sell to realize only profits"""
    service = PortfolioAdvancedService(db)
    
    try:
        result = service.calculate_sell_profits_only(
            user_id=current_user.id,
            investment_id=investment_id,
            target_amount=target_amount,
            current_price=current_price
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating sell amount: {str(e)}"
        )

@router.post("/sell-calculator/percentage")
def calculate_sell_percentage(
    investment_id: int = Query(..., gt=0),
    sell_percentage: float = Query(..., gt=0, le=100),
    current_price: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate sell details for a percentage of holdings"""
    service = PortfolioAdvancedService(db)
    
    try:
        result = service.calculate_sell_percentage(
            user_id=current_user.id,
            investment_id=investment_id,
            sell_percentage=sell_percentage,
            current_price=current_price
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating sell percentage: {str(e)}"
        )

# DIVIDEND ENDPOINTS
@router.post("/dividends", response_model=DividendOut, status_code=status.HTTP_201_CREATED)
def record_dividend(
    dividend_data: DividendCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a dividend payment"""
    service = PortfolioAdvancedService(db)
    
    try:
        dividend = service.record_dividend(
            user_id=current_user.id,
            investment_id=dividend_data.investment_id,
            amount_per_share=dividend_data.amount_per_share,
            total_shares=dividend_data.total_shares,
            payment_date=dividend_data.payment_date,
            ex_dividend_date=dividend_data.ex_dividend_date,
            currency=dividend_data.currency,
            tax_withheld=dividend_data.tax_withheld,
            tax_rate=dividend_data.tax_rate,
            reinvested=dividend_data.reinvested,
            payment_method=dividend_data.payment_method,
            notes=dividend_data.notes
        )
        return dividend
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording dividend: {str(e)}"
        )

@router.get("/dividends/summary")
def get_dividend_summary(
    year: Optional[int] = Query(None, gt=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dividend summary"""
    service = PortfolioAdvancedService(db)
    
    try:
        summary = service.get_dividend_summary(current_user.id, year)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dividend summary: {str(e)}"
        )

@router.get("/dividends", response_model=List[DividendOut])
def list_dividends(
    investment_id: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List dividends with filtering"""
    from app.models.dividend import Dividend
    from sqlalchemy import and_
    
    query = db.query(Dividend).filter(
        Dividend.user_id == current_user.id
    )
    
    if investment_id:
        query = query.filter(Dividend.investment_id == investment_id)
    
    if year:
        from sqlalchemy import extract
        query = query.filter(extract('year', Dividend.payment_date) == year)
    
    dividends = query.order_by(
        Dividend.payment_date.desc()
    ).offset(offset).limit(limit).all()
    
    return dividends

# INVESTMENT GOAL ENDPOINTS
@router.post("/goals", response_model=InvestmentGoalOut, status_code=status.HTTP_201_CREATED)
def create_investment_goal(
    goal_data: InvestmentGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new investment goal"""
    service = PortfolioAdvancedService(db)
    
    try:
        goal = service.create_investment_goal(
            user_id=current_user.id,
            name=goal_data.name,
            target_amount=goal_data.target_amount,
            target_date=goal_data.target_date,
            description=goal_data.description,
            monthly_contribution=goal_data.monthly_contribution,
            initial_investment=goal_data.initial_investment,
            risk_profile=goal_data.risk_profile
        )
        return goal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating investment goal: {str(e)}"
        )

@router.get("/goals", response_model=List[InvestmentGoalOut])
def list_investment_goals(
    active_only: bool = Query(True),
    achieved_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List investment goals"""
    from app.models.investment_goal import InvestmentGoal
    from sqlalchemy import and_
    
    query = db.query(InvestmentGoal).filter(
        InvestmentGoal.user_id == current_user.id
    )
    
    if active_only:
        query = query.filter(InvestmentGoal.is_active == True)
    
    if achieved_only:
        query = query.filter(InvestmentGoal.achieved == True)
    
    goals = query.order_by(
        InvestmentGoal.target_date.asc()
    ).all()
    
    return goals

@router.get("/goals/{goal_id}", response_model=InvestmentGoalOut)
def get_investment_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific investment goal"""
    from app.models.investment_goal import InvestmentGoal
    
    goal = db.query(InvestmentGoal).filter(
        and_(
            InvestmentGoal.id == goal_id,
            InvestmentGoal.user_id == current_user.id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment goal not found"
        )
    
    return goal

@router.put("/goals/{goal_id}", response_model=InvestmentGoalOut)
def update_investment_goal(
    goal_id: int,
    goal_data: InvestmentGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update investment goal"""
    from app.models.investment_goal import InvestmentGoal
    
    goal = db.query(InvestmentGoal).filter(
        and_(
            InvestmentGoal.id == goal_id,
            InvestmentGoal.user_id == current_user.id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment goal not found"
        )
    
    # Update fields
    update_data = goal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)
    
    goal.updated_at = datetime.now()
    db.commit()
    db.refresh(goal)
    
    return goal

@router.post("/goals/{goal_id}/contribute")
def contribute_to_goal(
    goal_id: int,
    amount: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Make a contribution to an investment goal"""
    service = PortfolioAdvancedService(db)
    
    try:
        goal = service.update_goal_progress(
            user_id=current_user.id,
            goal_id=goal_id,
            additional_amount=amount
        )
        return {
            "message": f"Successfully contributed ${amount:,.2f} to goal '{goal.name}'",
            "goal": InvestmentGoalOut.from_orm(goal)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating goal: {str(e)}"
        )

@router.get("/goals/{goal_id}/projection")
def get_goal_projection(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get future projection for investment goal"""
    service = PortfolioAdvancedService(db)
    
    try:
        projection = service.get_goal_projection(goal_id, current_user.id)
        return projection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating projection: {str(e)}"
        )

@router.get("/goals/alerts/check")
def check_goal_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check for investment goal alerts"""
    service = PortfolioAdvancedService(db)
    
    try:
        alerts = service.check_goals_alerts(current_user.id)
        return {
            "user_id": current_user.id,
            "alerts": alerts,
            "alert_count": len(alerts),
            "checked_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking alerts: {str(e)}"
        )

# PORTFOLIO HEALTH ENDPOINTS
@router.get("/health-score")
def get_portfolio_health_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate portfolio health score"""
    service = PortfolioAdvancedService(db)
    
    try:
        health_score = service.calculate_portfolio_health_score(current_user.id)
        return health_score
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating health score: {str(e)}"
        )

# PRICE ALERT ENDPOINTS (Basic Implementation)
@router.post("/alerts", response_model=PriceAlertOut, status_code=status.HTTP_201_CREATED)
def create_price_alert(
    alert_data: PriceAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a price alert"""
    from app.models.price_alert import PriceAlert
    
    alert = PriceAlert(
        user_id=current_user.id,
        symbol=alert_data.symbol,
        asset_type=alert_data.asset_type,
        alert_type=alert_data.alert_type,
        investment_id=alert_data.investment_id,
        target_price=alert_data.target_price,
        percent_change=alert_data.percent_change,
        current_price=alert_data.current_price,
        trigger_direction=alert_data.trigger_direction,
        expiration_date=alert_data.expiration_date,
        name=alert_data.name,
        notes=alert_data.notes,
        notify_email=alert_data.notify_email,
        notify_push=alert_data.notify_push,
        notify_sms=alert_data.notify_sms
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return alert

@router.get("/alerts", response_model=List[PriceAlertOut])
def list_price_alerts(
    active_only: bool = Query(True),
    triggered_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List price alerts"""
    from app.models.price_alert import PriceAlert
    from sqlalchemy import and_
    
    query = db.query(PriceAlert).filter(
        PriceAlert.user_id == current_user.id
    )
    
    if active_only:
        query = query.filter(PriceAlert.is_active == True)
    
    if triggered_only:
        query = query.filter(PriceAlert.triggered == True)
    
    alerts = query.order_by(
        PriceAlert.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return alerts

@router.put("/alerts/{alert_id}/trigger")
def trigger_price_alert(
    alert_id: int,
    trigger_price: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a price alert as triggered"""
    from app.models.price_alert import PriceAlert
    from sqlalchemy import and_
    
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == current_user.id,
            PriceAlert.is_active == True,
            PriceAlert.triggered == False
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found or already triggered"
        )
    
    alert.triggered = True
    alert.triggered_at = datetime.now()
    alert.triggered_price = trigger_price
    alert.is_active = False
    
    db.commit()
    
    return {
        "message": "Alert triggered successfully",
        "alert_id": alert_id,
        "triggered_at": alert.triggered_at,
        "triggered_price": trigger_price
    }

# DASHBOARD SUMMARY ENDPOINT
@router.get("/dashboard")
def get_advanced_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard data"""
    service = PortfolioAdvancedService(db)
    
    try:
        # Get multiple data points in parallel (in production)
        health_score = service.calculate_portfolio_health_score(current_user.id)
        rebalancing_recs = service.get_rebalancing_recommendations(current_user.id)
        dividend_summary = service.get_dividend_summary(current_user.id)
        goal_alerts = service.check_goals_alerts(current_user.id)
        
        # Get basic goals list
        from app.models.investment_goal import InvestmentGoal
        goals = db.query(InvestmentGoal).filter(
            InvestmentGoal.user_id == current_user.id,
            InvestmentGoal.is_active == True
        ).order_by(InvestmentGoal.target_date.asc()).limit(5).all()
        
        # Get active alerts
        from app.models.price_alert import PriceAlert
        active_alerts = db.query(PriceAlert).filter(
            PriceAlert.user_id == current_user.id,
            PriceAlert.is_active == True
        ).order_by(PriceAlert.created_at.desc()).limit(10).all()
        
        return {
            "health_score": health_score,
            "rebalancing": rebalancing_recs,
            "dividends": dividend_summary,
            "goal_alerts": goal_alerts,
            "goals_summary": [
                {
                    "id": g.id,
                    "name": g.name,
                    "progress": g.progress_percentage,
                    "target_date": g.target_date,
                    "months_remaining": service._calculate_months_remaining(g.target_date)
                }
                for g in goals
            ],
            "active_alerts": len(active_alerts),
            "dashboard_updated": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard: {str(e)}"
        )