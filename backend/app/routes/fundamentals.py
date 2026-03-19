from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.fundamentals_service import get_fundamentals
from app.schemas.fundamentals import FundamentalsResponse

router = APIRouter(prefix="/fundamentals", tags=["Fundamentals"])


@router.get("/{symbol}", response_model=FundamentalsResponse)
async def fundamentals_endpoint(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_fundamentals(symbol, db)