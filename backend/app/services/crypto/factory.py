from sqlalchemy.orm import Session
from .crypto_service import CryptoService
from .real_time_service import CryptoRealTimeService

class CryptoServiceFactory:
    _instances = {}
    
    @classmethod
    def create_crypto_service(cls, db: Session) -> CryptoService:
        """Create or reuse CryptoService instance"""
        key = id(db)
        if key not in cls._instances:
            cls._instances[key] = CryptoService(db)
        return cls._instances[key]
    
    @classmethod
    def create_real_time_service(cls, crypto_service: CryptoService) -> CryptoRealTimeService:
        """Create RealTimeService instance"""
        return CryptoRealTimeService(crypto_service)