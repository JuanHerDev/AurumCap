# routers/crypto_enhanced.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import asyncio

from app.db.database import get_db
from app.deps.auth import get_current_user
from app.services.crypto.enhanced_crypto_service import EnhancedCryptoService
from app.services.crypto.auto_updater import CryptoAutoUpdater
from app.models.user import User

router = APIRouter(prefix="/crypto/v2", tags=["crypto-enhanced"])

# Instancia global del auto-updater
_auto_updater = None

def get_auto_updater(db: Session = Depends(get_db)) -> CryptoAutoUpdater:
    """Obtener instancia del auto-updater"""
    global _auto_updater
    if _auto_updater is None:
        crypto_service = EnhancedCryptoService(db)
        _auto_updater = CryptoAutoUpdater(db, crypto_service)
        # Iniciar actualizaciones automáticas
        _auto_updater.start_auto_updates(interval_minutes=5)
    return _auto_updater

@router.get("/universal-search")
async def universal_crypto_search(
    query: str = Query(..., min_length=1, description="Nombre, símbolo o ID de la cripto"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Búsqueda universal de CUALQUIER criptomoneda"""
    crypto_service = EnhancedCryptoService(db)
    
    results = await crypto_service.universal_crypto_search(query)
    
    return {
        "query": query,
        "results_count": len(results),
        "results": results
    }

@router.get("/any/{identifier}")
def get_any_crypto_info(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener información de CUALQUIER cripto usando símbolo, nombre o ID"""
    crypto_service = EnhancedCryptoService(db)
    
    crypto_info = crypto_service.get_any_crypto_info(identifier)
    if not crypto_info:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontró la criptomoneda: {identifier}"
        )
    
    return crypto_info

@router.get("/auto-update/status")
def get_auto_update_status(
    auto_updater: CryptoAutoUpdater = Depends(get_auto_updater),
    current_user: User = Depends(get_current_user)
):
    """Obtener estado del auto-updater"""
    return {
        "is_running": auto_updater.is_running,
        "last_update": auto_updater.last_update,
        "cached_prices_count": len(auto_updater.price_cache)
    }

@router.post("/auto-update/force")
def force_auto_update(
    background_tasks: BackgroundTasks,
    auto_updater: CryptoAutoUpdater = Depends(get_auto_updater),
    current_user: User = Depends(get_current_user)
):
    """Forzar actualización inmediata de precios"""
    background_tasks.add_task(auto_updater.force_update)
    
    return {"message": "Actualización forzada iniciada en segundo plano"}

@router.get("/prices/cached")
def get_cached_prices(
    symbol: Optional[str] = None,
    auto_updater: CryptoAutoUpdater = Depends(get_auto_updater),
    current_user: User = Depends(get_current_user)
):
    """Obtener precios desde cache (rápido)"""
    if symbol:
        price_data = auto_updater.get_cached_price(symbol)
        if not price_data:
            raise HTTPException(status_code=404, detail=f"Precio no encontrado para: {symbol}")
        return price_data
    else:
        return auto_updater.get_all_cached_prices()

@router.get("/discover/trending")
async def get_trending_discovery(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Descubrir cryptos trending"""
    crypto_service = EnhancedCryptoService(db)
    
    try:
        trending = crypto_service.cg.get_search_trending()
        trending_coins = []
        
        for coin in trending.get('coins', [])[:10]:
            coin_data = coin.get('item', {})
            market_data = await crypto_service._get_quick_market_data(coin_data.get('id'))
            
            trending_coins.append({
                'coin_id': coin_data.get('id'),
                'name': coin_data.get('name'),
                'symbol': coin_data.get('symbol'),
                'market_cap_rank': coin_data.get('market_cap_rank'),
                'thumb': coin_data.get('thumb'),
                'market_data': market_data
            })
        
        return {"trending": trending_coins}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error obteniendo trending coins")

@router.get("/discover/categories")
def get_crypto_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener categorías de criptomonedas"""
    crypto_service = EnhancedCryptoService(db)
    
    try:
        categories = crypto_service.cg.get_coins_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error obteniendo categorías")