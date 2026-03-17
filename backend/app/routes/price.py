from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.asset import Asset
from app.services.price_service import get_price

router = APIRouter(
    prefix="/price", tags=["Prices"]
)

@router.get("/{symbol}")
def price(symbol: str, db: Session = Depends(get_db)):

    asset = db.query(Asset).filter(
        Asset.symbol == symbol.upper()
    ).first()

    if not asset:
        return {"error": "asset not found"}
    
    price = get_price(asset)

    return {
        "symbol": symbol,
        "price": price
    }
