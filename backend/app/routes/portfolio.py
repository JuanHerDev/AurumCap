from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.portfolio_service import calculate_portfolio

router = APIRouter(
    prefix="/portfolio", tags=["portfolio"]
)

@router.get("/{user_id}")
def get_portfolio(user_id: int, db: Session = Depends(get_db)):

    portfolio = calculate_portfolio(db, user_id)

    return {
        "portfolio": portfolio
    }