# services/stocks/factory.py
from sqlalchemy.orm import Session
from .stock_service import StockService
from .real_time_service import StockRealTimeService

class StockServiceFactory:
    _instances = {}
    
    @classmethod
    def create_stock_service(cls, db: Session) -> StockService:
        """Create or reuse StockService instance"""
        key = id(db)
        if key not in cls._instances:
            cls._instances[key] = StockService(db)
        return cls._instances[key]
    
    @classmethod
    def create_real_time_service(cls, stock_service: StockService) -> StockRealTimeService:
        """Create RealTimeService instance"""
        return StockRealTimeService(stock_service)