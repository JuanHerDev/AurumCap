from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.portfolio_service import get_portfolio
from app.schemas.portfolio import PortfolioResponse

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/me", response_model=PortfolioResponse)
async def portfolio_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_portfolio(current_user.id, db)
