# services/crypto/auto_updater.py
import asyncio
import schedule
import time
from threading import Thread
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from app.services.crypto.enhanced_crypto_service import EnhancedCryptoService
from app.models.crypto.crypto_models import CryptoSymbolMapping

logger = logging.getLogger(__name__)

class CryptoAutoUpdater:
    def __init__(self, db: Session, crypto_service: EnhancedCryptoService):
        self.db = db
        self.crypto_service = crypto_service
        self.is_running = False
        self.update_thread = None
        
        # Cache de precios actualizados
        self.price_cache = {}
        self.last_update = None
    
    def start_auto_updates(self, interval_minutes: int = 5):
        """Iniciar actualizaciones automáticas"""
        if self.is_running:
            logger.warning("Auto-updater ya está ejecutándose")
            return
        
        self.is_running = True
        self.update_thread = Thread(target=self._run_scheduler, daemon=True)
        self.update_thread.start()
        
        logger.info(f"Auto-updater iniciado con intervalo de {interval_minutes} minutos")
    
    def stop_auto_updates(self):
        """Detener actualizaciones automáticas"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("Auto-updater detenido")
    
    def _run_scheduler(self):
        """Ejecutar el planificador en un hilo separado"""
        # Actualizar inmediatamente al iniciar
        self._update_all_prices()
        
        # Programar actualizaciones periódicas
        schedule.every(5).minutes.do(self._update_all_prices)
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Revisar cada minuto
    
    def _update_all_prices(self):
        """Refresh prices of all cryptos in db"""
        try:
            
            logger.info("Starting automatic price update...")
            
            # Get all active symbols
            mappings = self.db.query(CryptoSymbolMapping).filter(
                CryptoSymbolMapping.is_active == True
            ).all()
            
            symbols = [mapping.symbol for mapping in mappings]
            
            if not symbols:
                logger.warning("There are no symbols to update")
                return
            
            # Update prices in bulk
            updated_prices = {}
            for symbol in symbols:
                price_data = self.crypto_service.get_current_price(symbol)
                if price_data:
                    updated_prices[symbol] = price_data
                
                # Short break to avoid rate limiting
                time.sleep(0.1)
            
            # Update cache
            self.price_cache = updated_prices
            self.last_update = datetime.now()
            
            logger.info(f"Update complete: {len(updated_prices)} updated prices")
            
        except Exception as e:
            logger.error(f"Error in automatic update: {str(e)}")
    
    def get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price from cache"""
        symbol = symbol.upper()
        return self.price_cache.get(symbol)
    
    def get_all_cached_prices(self) -> Dict[str, Any]:
        """Get all cached prices"""
        return {
            'prices': self.price_cache,
            'last_update': self.last_update,
            'total_cryptos': len(self.price_cache)
        }
    
    def force_update(self, symbols: List[str] = None):
        """Force immediate update"""
        logger.info("Forcing price update...")
        self._update_all_prices()