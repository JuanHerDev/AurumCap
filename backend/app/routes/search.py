from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.search_service import search_assets
from app.schemas.search import SearchResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
async def search_endpoint(
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await search_assets(q, db, limit)