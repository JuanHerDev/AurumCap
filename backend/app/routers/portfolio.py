from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.database import get_db
from app.deps.auth import get_current_user
from app.crud.portfolio_crud import PortfolioCRUD
from app.models.user import User
from app.schemas.portfolio import (
    InvestmentCardResponse,
    InvestmentModalResponse,
    PortfolioSummaryResponse,
    AllocationResponse,
    PerformanceResponse
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/investment-cards", response_model=List[InvestmentCardResponse])
def get_investment_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data formatted specifically for investment cards"""
    crud = PortfolioCRUD(db)
    cards_data = crud.get_investment_cards_data(current_user.id)
    return cards_data

@router.get("/investment-detail/{investment_id}", response_model=InvestmentModalResponse)
def get_investment_modal_data(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed data for investment modal"""
    crud = PortfolioCRUD(db)
    detail = crud.get_investment_modal_data(investment_id, current_user.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Investment not found")
    return InvestmentModalResponse(**detail)

@router.get("/sparkline/{symbol}")
def get_sparkline_data(
    symbol: str,
    asset_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sparkline data for investment cards"""
    crud = PortfolioCRUD(db)
    
    if asset_type == 'crypto':
        sparkline_data = crud.crypto_service.get_sparkline_data(symbol, days=7)
        return {"symbol": symbol, "sparkline_data": sparkline_data}
    else:
        # Para stocks, podrías integrar con TwelveData
        return {"symbol": symbol, "sparkline_data": []}


@router.get("/investments", response_model=PortfolioSummaryResponse)
def get_user_investments(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all investments for current user with portfolio summary"""
    crud = PortfolioCRUD(db)
    summary = crud.get_portfolio_summary(current_user.id)
    return PortfolioSummaryResponse(**summary)

@router.get("/investments/{investment_id}", response_model=InvestmentModalResponse)
def get_investment_detail(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed investment information for modal view"""
    crud = PortfolioCRUD(db)
    detail = crud.get_investment_detail(investment_id, current_user.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Investment not found")
    return InvestmentModalResponse(**detail)

@router.post("/investments", response_model=Dict[str, Any])
def create_investment(
    investment_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new investment"""
    crud = PortfolioCRUD(db)
    
    # Extract required fields
    required_fields = ['symbol', 'asset_type']
    for field in required_fields:
        if field not in investment_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    investment = crud.create_investment(
        user_id=current_user.id,
        symbol=investment_data['symbol'],
        asset_type=investment_data['asset_type'],
        platform_id=investment_data.get('platform_id'),
        quantity=investment_data.get('quantity', 0),
        invested_amount=investment_data.get('invested_amount', 0),
        purchase_price=investment_data.get('purchase_price', 0),
        currency=investment_data.get('currency', 'USD'),
        notes=investment_data.get('notes')
    )
    
    return {"message": "Investment created successfully", "investment": investment.to_dict()}

@router.put("/investments/{investment_id}", response_model=Dict[str, Any])
def update_investment(
    investment_id: int,
    investment_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an investment"""
    crud = PortfolioCRUD(db)
    
    investment = crud.update_investment(investment_id, current_user.id, **investment_data)
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    return {"message": "Investment updated successfully", "investment": investment.to_dict()}

@router.delete("/investments/{investment_id}")
def delete_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an investment"""
    crud = PortfolioCRUD(db)
    
    success = crud.delete_investment(investment_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    return {"message": "Investment deleted successfully"}

@router.post("/investments/{investment_id}/transactions")
def add_transaction(
    investment_id: int,
    transaction_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a transaction to an investment"""
    crud = PortfolioCRUD(db)
    
    required_fields = ['transaction_type', 'quantity', 'price']
    for field in required_fields:
        if field not in transaction_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Verify investment belongs to user
    investment = crud.get_investment_by_id(investment_id, current_user.id)
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    transaction = crud.add_transaction(
        investment_id=investment_id,
        transaction_type=transaction_data['transaction_type'],
        quantity=transaction_data['quantity'],
        price=transaction_data['price'],
        fees=transaction_data.get('fees', 0),
        platform_id=transaction_data.get('platform_id'),
        notes=transaction_data.get('notes')
    )
    
    return {"message": "Transaction added successfully", "transaction_id": transaction.id}

@router.get("/analytics/allocations", response_model=AllocationResponse)
def get_portfolio_allocations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio allocations"""
    crud = PortfolioCRUD(db)
    allocations = crud.get_portfolio_allocations(current_user.id)
    return AllocationResponse(**allocations)

@router.get("/analytics/performance", response_model=PerformanceResponse)
def get_performance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio performance metrics"""
    crud = PortfolioCRUD(db)
    performance = crud.get_performance_metrics(current_user.id)
    return PerformanceResponse(**performance)