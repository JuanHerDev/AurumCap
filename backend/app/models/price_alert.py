from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.database import Base

class PriceAlert(Base):
    """
    Model for tracking price alerts for investments.
    
    Users can set alerts for specific price levels or percentage changes
    and receive notifications when conditions are met.
    """
    __tablename__ = "price_alerts"
    __table_args__ = {'extend_existing': True}  # Prevent duplicate table definition error
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, doc="Primary key identifier")
    
    # User and investment references
    user_id = Column(Integer, nullable=False, index=True, doc="ID of the user who created the alert")
    investment_id = Column(Integer, nullable=True, index=True, doc="Optional reference to a specific investment")
    
    # Alert configuration
    symbol = Column(String(20), nullable=False, doc="Ticker symbol or asset identifier (e.g., AAPL, BTC-USD)")
    asset_type = Column(String(20), nullable=False, doc="Type of asset: stock, crypto, bond, etc.")
    alert_type = Column(String(20), nullable=False, doc="Type of alert: price_target, percent_change, moving_average")
    
    # Trigger conditions
    target_price = Column(Float, nullable=True, doc="Target price for price_target alerts")
    percent_change = Column(Float, nullable=True, doc="Percentage change threshold for percent_change alerts")
    current_price = Column(Float, nullable=False, doc="Price at the time the alert was created")
    trigger_direction = Column(String(10), default="both", doc="Direction to trigger: above, below, or both")
    
    # Timing and expiration
    expiration_date = Column(DateTime, nullable=True, doc="Optional date when the alert expires")
    created_at = Column(DateTime, server_default=func.now(), doc="Timestamp when alert was created")
    
    # Status tracking
    is_active = Column(Boolean, default=True, doc="Whether the alert is currently active")
    triggered = Column(Boolean, default=False, doc="Whether the alert has been triggered")
    triggered_at = Column(DateTime, doc="Timestamp when alert was triggered (if applicable)")
    triggered_price = Column(Float, doc="Price at which alert was triggered (if applicable)")
    
    # Notification preferences
    notify_email = Column(Boolean, default=True, doc="Send email notifications for this alert")
    notify_push = Column(Boolean, default=True, doc="Send push notifications for this alert")
    notify_sms = Column(Boolean, default=False, doc="Send SMS notifications for this alert")
    
    # Descriptive metadata
    name = Column(String(100), doc="Optional name for the alert (e.g., 'Apple $150 Alert')")
    notes = Column(String(500), doc="Optional notes or comments about the alert")