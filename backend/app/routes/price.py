from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.price_service import get_price
from app.schemas.price import PriceResponse

router = APIRouter(prefix="/price", tags=["Prices"])


@router.get("/{symbol}", response_model=PriceResponse)
async def price_endpoint(symbol: str, db: AsyncSession = Depends(get_db)):
    return await get_price(symbol, db)