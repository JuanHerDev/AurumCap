from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.crypto.factory import CryptoServiceFactory
from app.models.crypto.crypto_models import CryptoSymbolMapping

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/crypto-price/{symbol}")
def debug_crypto_price(symbol: str, db: Session = Depends(get_db)):
    """Debug endpoint to check crypto price fetching with detailed info"""
    crypto_service = CryptoServiceFactory.create_crypto_service(db)
    
    # Test coin ID mapping with detailed info
    coin_id = crypto_service._get_coin_id_from_symbol(symbol)
    
    # Check database mappings
    db_mappings = db.query(CryptoSymbolMapping).filter(
        CryptoSymbolMapping.symbol == symbol.upper()
    ).all()
    
    # Test direct price fetch
    price_data = crypto_service.get_current_price(symbol)
    
    # Test CoinGecko API directly
    try:
        cg_data = crypto_service.cg.get_price(ids='bitcoin', vs_currencies='usd')
    except Exception as e:
        cg_data = f"Error: {str(e)}"
    
    # Test with common mappings
    common_mapping = crypto_service.common_mappings.get(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "coin_id_from_method": coin_id,
        "common_mapping": common_mapping,
        "database_mappings": [{"symbol": m.symbol, "coingecko_id": m.coingecko_id} for m in db_mappings],
        "price_data": price_data,
        "coingecko_direct_test": cg_data,
        "common_mappings_available": list(crypto_service.common_mappings.keys())[:10]  # First 10
    }

@router.get("/database-mappings")
def debug_database_mappings(db: Session = Depends(get_db)):
    """Check all cryptocurrency mappings in database"""
    mappings = db.query(CryptoSymbolMapping).all()
    return {
        "total_mappings": len(mappings),
        "mappings": [{"symbol": m.symbol, "coingecko_id": m.coingecko_id, "active": m.is_active} for m in mappings]
    }