from sqlalchemy import Column, Integer, Float, ForeignKey
from app.db.base import Base

class Holdings(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))

    quantity = Column(Float)
    avg_price = Column(Float)