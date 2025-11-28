# scripts/populate_crypto_mappings.py - Quick fix for crypto mappings
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.crypto.crypto_models import CryptoSymbolMapping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_crypto_mappings_quick():
    """Quick population of cryptocurrency mappings - SOLVES THE PRICE ISSUE"""
    db = SessionLocal()
    
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
                # Create new mapping
                symbol_mapping = CryptoSymbolMapping(
                    symbol=crypto['symbol'],
                    coingecko_id=crypto['coingecko_id'],
                    is_active=True,
                    created_at=datetime.now()
                )
                db.add(symbol_mapping)
                added_count += 1
                logger.info(f"✅ Added: {crypto['symbol']} -> {crypto['coingecko_id']}")
            else:
                logger.info(f"✓ Exists: {crypto['symbol']} -> {existing.coingecko_id}")
                
        except Exception as e:
            logger.error(f"❌ Error with {crypto['symbol']}: {e}")
            db.rollback()
    
    db.commit()
    db.close()
    
    logger.info(f"🎉 Successfully added {added_count} cryptocurrency mappings")
    logger.info("🚀 Your portfolio should now show real prices!")

if __name__ == "__main__":
    populate_crypto_mappings_quick()