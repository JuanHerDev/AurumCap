from sqlalchemy import Column, String, Float, Date, DateTime
from datetime import datetime
from app.db.database import Base

class EconomicData(Base):
    __tablename__ = "economic_data"
    
    indicator_code = Column(String(50), primary_key=True)
    indicator_name = Column(String(200), nullable=False)
    country = Column(String(50), nullable=False)
    frequency = Column(String(20))
    current_value = Column(Float)
    previous_value = Column(Float)
    unit = Column(String(50))
    last_update_date = Column(Date, nullable=False)
    next_update_date = Column(Date)
    last_updated = Column(DateTime, default=datetime.now)
    cache_until = Column(DateTime, nullable=False)

class EconomicCalendarCache(Base):
    __tablename__ = "economic_calendar_cache"
    
    event_id = Column(String(100), primary_key=True)
    event_name = Column(String(200), nullable=False)
    country = Column(String(50), nullable=False)
    importance = Column(String(10))
    event_date = Column(DateTime, nullable=False)
    actual_value = Column(Float)
    forecast_value = Column(Float)
    previous_value = Column(Float)
    last_updated = Column(DateTime, default=datetime.now)
    cache_strategy = Column(String(20))