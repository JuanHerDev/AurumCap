from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)

    asset_id = Column(Integer, ForeignKey("assets.id"))

    title = Column(String)
    url = Column(String)

    published_at = Column(DateTime, default=datetime.utcnow)

    source = Column(String)

    asset = relationship("Asset", back_populates="news")