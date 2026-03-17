from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.portfolio_service import get_portfolio
from app.schemas.portfolio import PortfolioResponse

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/{user_id}", response_model=PortfolioResponse)
async def portfolio_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_portfolio(user_id, db)
