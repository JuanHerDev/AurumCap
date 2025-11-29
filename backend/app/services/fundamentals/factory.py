# services/fundamentals/factory.py
from sqlalchemy.orm import Session
from .fundamentals_service import FundamentalsService

class FundamentalsServiceFactory:
    _instances = {}
    
    @classmethod
    def create_fundamentals_service(cls, db: Session) -> FundamentalsService:
        """Create or reuse FundamentalsService instance"""
        key = id(db)
        if key not in cls._instances:
            cls._instances[key] = FundamentalsService(db)
        return cls._instances[key]