from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.asset import Asset
from app.services.price_service import get_price

router = APIRouter(
    prefix="/search", tags=["Search Assets"]
)

@router.get("")
def search_assets(q: str, db: Session = Depends(get_db)):

    assets = db.query(Asset).filter(
        Asset.symbol.ilike(f"%{q}%") |
        Asset.name.ilike(f"%{q}%")
    ).limit(20).all()

    return assets