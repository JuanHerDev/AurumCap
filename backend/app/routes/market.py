from fastapi import APIRouter

from app.services.market_service import get_market_status
from app.schemas.market import MarketStatusResponse

router = APIRouter(prefix="/market", tags=["Market"])


@router.get("/status", response_model=MarketStatusResponse)
async def market_status_endpoint():
    return await get_market_status()