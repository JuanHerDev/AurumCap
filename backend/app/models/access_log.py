from sqlalchemy import Column, Integer, Float, DateTime, text, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.database import Base

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ip = Column(String(45))
    method = Column(String(10))
    path = Column(String)
    user_agent = Column(String)
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    create_at = Column(DateTime(timezone=True), server_default=text('NOW()'), nullable=False)