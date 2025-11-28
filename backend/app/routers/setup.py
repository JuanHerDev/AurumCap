from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.database import get_db
from app.models.crypto.crypto_models import CryptoSymbolMapping, CryptoCategory
from app.models.stocks.stock_models import StockSector, StockExchange

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/setup", tags=["setup"])

@router.post("/crypto-mappings")
def setup_crypto_mappings(db: Session = Depends(get_db)):
    """Setup common cryptocurrency mappings in database"""
    
    common_cryptos = [
        {'symbol': 'BTC', 'coingecko_id': 'bitcoin'},
        {'symbol': 'ETH', 'coingecko_id': 'ethereum'},
        {'symbol': 'ADA', 'coingecko_id': 'cardano'},
        {'symbol': 'DOT', 'coingecko_id': 'polkadot'},
        {'symbol': 'LINK', 'coingecko_id': 'chainlink'},
        {'symbol': 'LTC', 'coingecko_id': 'litecoin'},
        {'symbol': 'BCH', 'coingecko_id': 'bitcoin-cash'},
        {'symbol': 'XRP', 'coingecko_id': 'ripple'},
        {'symbol': 'SOL', 'coingecko_id': 'solana'},
        {'symbol': 'AVAX', 'coingecko_id': 'avalanche-2'},
        {'symbol': 'MATIC', 'coingecko_id': 'matic-network'},
        {'symbol': 'DOGE', 'coingecko_id': 'dogecoin'},
        {'symbol': 'ATOM', 'coingecko_id': 'cosmos'},
        {'symbol': 'XLM', 'coingecko_id': 'stellar'},
        {'symbol': 'EOS', 'coingecko_id': 'eos'},
        {'symbol': 'BNB', 'coingecko_id': 'binancecoin'},
        {'symbol': 'USDT', 'coingecko_id': 'tether'},
        {'symbol': 'USDC', 'coingecko_id': 'usd-coin'},
    ]
    
    added_count = 0
    for crypto in common_cryptos:
        try:
            # Check if mapping already exists
            existing = db.query(CryptoSymbolMapping).filter(
                CryptoSymbolMapping.symbol == crypto['symbol']
            ).first()
            
            if not existing:
                new_mapping = CryptoSymbolMapping(
                    symbol=crypto['symbol'],
                    coingecko_id=crypto['coingecko_id'],
                    is_active=True,
                    created_at=datetime.now()
                )
                db.add(new_mapping)
                added_count += 1
                logger.info(f"Added: {crypto['symbol']} -> {crypto['coingecko_id']}")
            else:
                logger.info(f"Already exists: {crypto['symbol']} -> {existing.coingecko_id}")
                
        except Exception as e:
            logger.error(f"Error with {crypto['symbol']}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error setting up mappings: {str(e)}")
    
    db.commit()
    
    return {
        "message": f"Added {added_count} new cryptocurrency mappings",
        "total_mappings": len(common_cryptos),
        "status": "success"
    }

@router.get("/status")
def setup_status(db: Session = Depends(get_db)):
    """Check current setup status"""
    crypto_mappings_count = db.query(CryptoSymbolMapping).count()
    crypto_categories_count = db.query(CryptoCategory).count()
    stock_sectors_count = db.query(StockSector).count()
    stock_exchanges_count = db.query(StockExchange).count()
    
    return {
        "crypto_mappings": crypto_mappings_count,
        "crypto_categories": crypto_categories_count,
        "stock_sectors": stock_sectors_count,
        "stock_exchanges": stock_exchanges_count,
        "status": "ready" if crypto_mappings_count > 0 else "needs_setup"
    }