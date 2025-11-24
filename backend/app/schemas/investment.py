from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
import re
import logging

logger = logging.getLogger(__name__)

# CONSTANTS
SYMBOL_REGEX = re.compile(r"^[A-Za-z0-9\.\-\_]{1,64}$")
MAX_DECIMAL_DIGITS = 28
MAX_DECIMAL_PLACES = 10

# DECIMAL SERIALIZER
def clean_decimal(v: Decimal) -> str:
    """
    Safe decimal serialization with rounding for JSON compatibility
    """
    if v is None:
        return None
    
    try:
        # Round to avoid floating point issues
        rounded = v.quantize(Decimal('0.0000000001'), rounding=ROUND_HALF_UP)
        # Normalize to remove trailing zeros
        normalized = rounded.normalize()
        return format(normalized, 'f')
    except Exception as e:
        logger.error(f"Error serializing decimal {v}: {e}")
        return str(v)

# ENUMS
class AssetType(str, Enum):
    crypto = "crypto"
    stock = "stock"
    etf = "etf"
    bond = "bond"
    real_estate = "real_estate"
    other = "other"

class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    COP = "COP"
    GBP = "GBP"
    JPY = "JPY"
    BTC = "BTC"
    ETH = "ETH"

class InvestmentStatus(str, Enum):
    active = "active"
    sold = "sold"
    closed = "closed"

# BASE MODEL
class InvestmentBase(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_encoders={Decimal: clean_decimal},
        validate_assignment=True,
        extra='forbid'
    )

    # Core investment fields
    asset_type: AssetType = Field(
        default=AssetType.other,
        description="Type of asset"
    )
    
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Asset symbol/ticker"
    )
    
    asset_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Full name of the asset"
    )

    # Financial fields
    invested_amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=18,
        decimal_places=6,
        description="Total amount invested"
    )
    
    quantity: Decimal = Field(
        ...,
        gt=0,
        max_digits=28,
        decimal_places=10,
        description="Quantity of asset purchased"
    )
    
    purchase_price: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=18,
        decimal_places=6,
        description="Price per unit at purchase"
    )
    
    currency: CurrencyEnum = Field(
        default=CurrencyEnum.USD,
        description="Currency of the investment"
    )
    

    # Field validators
    @field_validator('symbol', mode='before')
    @classmethod
    def validate_symbol_format(cls, v):
        """Validate and normalize symbol"""
        if not v or not isinstance(v, str):
            raise ValueError('Symbol must be a non-empty string')
            
        v = v.strip()
        if not v:
            raise ValueError('Symbol cannot be empty')
            
        if not SYMBOL_REGEX.fullmatch(v):
            raise ValueError(
                'Invalid symbol format. Only letters, numbers, dots, hyphens, and underscores are allowed'
            )
            
        return v.upper()

    @field_validator('invested_amount', 'quantity', 'purchase_price', mode='before')
    @classmethod
    def validate_and_convert_decimal(cls, v):
        """Validate and convert to Decimal"""
        if v is None:
            return None
            
        try:
            # Handle string, float, int inputs
            if isinstance(v, (int, float)):
                decimal_value = Decimal(str(v))
            elif isinstance(v, str):
                decimal_value = Decimal(v.strip())
            elif isinstance(v, Decimal):
                decimal_value = v
            else:
                raise ValueError(f"Unsupported type: {type(v)}")
                
            # Validate positive
            if decimal_value < 0:
                raise ValueError("Value must be positive")
                
            return decimal_value
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid decimal value: {v}") from e

    @model_validator(mode='after')
    def validate_purchase_price_consistency(self):
        """
        Validate that purchase_price is consistent with invested_amount and quantity
        """
        invested_amount = self.invested_amount
        quantity = self.quantity
        
        if invested_amount is not None and quantity is not None:
            calculated_price = invested_amount / quantity
            
            if self.purchase_price is not None:
                # If both are provided, they should be consistent within a small tolerance
                tolerance = Decimal('0.01')  # 1% tolerance
                price_diff = abs(self.purchase_price - calculated_price)
                avg_price = (self.purchase_price + calculated_price) / Decimal('2')
                
                if avg_price > 0 and (price_diff / avg_price) > tolerance:
                    logger.warning(
                        f"Purchase price inconsistency: "
                        f"provided={self.purchase_price}, calculated={calculated_price}"
                    )
            else:
                # Auto-calculate if not provided
                self.purchase_price = calculated_price.quantize(
                    Decimal('0.000001'), 
                    rounding=ROUND_HALF_UP
                )
                
        return self

# CREATE MODEL
class InvestmentCreate(InvestmentBase):
    """Schema for creating new investments"""
    
    # External IDs for API integrations
    coingecko_id: Optional[str] = Field(
        None,
        max_length=128,
        description="CoinGecko API ID"
    )
    
    twelvedata_id: Optional[str] = Field(
        None,
        max_length=128,
        description="TwelveData API ID"
    )
    
    platform_id: Optional[int] = Field(
        None,
        ge=1,
        description="ID of the platform where asset is held"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the investment"
    )

    @field_validator('coingecko_id', 'twelvedata_id', mode='before')
    @classmethod
    def validate_api_ids(cls, v):
        """Validate API IDs"""
        if v is not None and not isinstance(v, str):
            raise ValueError('API ID must be a string')
        return v

    @field_validator('platform_id', mode='before')
    @classmethod
    def validate_platform_id(cls, v):
        """Validate platform ID"""
        if v is not None and v < 1:
            raise ValueError('Platform ID must be positive')
        return v

# UPDATE MODEL
class InvestmentUpdate(BaseModel):
    """Schema for updating investments (partial updates)"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_encoders={Decimal: clean_decimal},
        validate_assignment=True,
        extra='forbid'
    )

    # Optional fields for partial updates
    symbol: Optional[str] = Field(
        None,
        min_length=1,
        max_length=64,
        description="Asset symbol/ticker"
    )
    
    asset_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Full name of the asset"
    )
    
    asset_type: Optional[AssetType] = Field(
        None,
        description="Type of asset"
    )
    
    invested_amount: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=18,
        decimal_places=6,
        description="Total amount invested"
    )
    
    quantity: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=28,
        decimal_places=10,
        description="Quantity of asset purchased"
    )
    
    purchase_price: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=18,
        decimal_places=6,
        description="Price per unit at purchase"
    )
    
    currency: Optional[CurrencyEnum] = Field(
        None,
        description="Currency of the investment"
    )
    
    
    platform_id: Optional[int] = Field(
        None,
        ge=1,
        description="ID of the platform where asset is held"
    )
    
    coingecko_id: Optional[str] = Field(
        None,
        max_length=128,
        description="CoinGecko API ID"
    )
    
    twelvedata_id: Optional[str] = Field(
        None,
        max_length=128,
        description="TwelveData API ID"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the investment"
    )

    # Reuse validators from base
    _validate_symbol = field_validator('symbol', mode='before')(InvestmentBase.validate_symbol_format)
    _validate_decimals = field_validator('invested_amount', 'quantity', 'purchase_price', mode='before')(
        InvestmentBase.validate_and_convert_decimal
    )

    @model_validator(mode='after')
    def validate_update_consistency(self):
        """
        Validate that updated fields maintain consistency
        """
        updates = self.model_dump(exclude_unset=True)
        
        # Check if we're updating financial fields that need consistency
        financial_fields = {'invested_amount', 'quantity', 'purchase_price'}
        updated_financial_fields = financial_fields.intersection(updates.keys())
        
        if len(updated_financial_fields) >= 2:
            # If multiple financial fields are updated, ensure consistency
            invested_amount = self.invested_amount
            quantity = self.quantity
            purchase_price = self.purchase_price
            
            if invested_amount and quantity and purchase_price:
                calculated_price = invested_amount / quantity
                tolerance = Decimal('0.01')  # 1% tolerance
                price_diff = abs(purchase_price - calculated_price)
                avg_price = (purchase_price + calculated_price) / Decimal('2')
                
                if avg_price > 0 and (price_diff / avg_price) > tolerance:
                    raise ValueError(
                        f"Inconsistent financial data: "
                        f"purchase_price={purchase_price}, "
                        f"calculated from invested/quantity={calculated_price}"
                    )
        
        return self

# RESPONSE MODELS
class InvestmentInDBBase(BaseModel):
    """Base model for database responses"""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={Decimal: clean_decimal}
    )

    # Database fields
    id: int = Field(..., description="Unique investment ID")
    user_id: int = Field(..., description="Owner user ID")
    platform_id: Optional[int] = Field(None, description="Platform ID")
    
    # Core investment fields
    asset_type: AssetType = Field(..., description="Type of asset")
    symbol: str = Field(..., description="Asset symbol/ticker")
    asset_name: Optional[str] = Field(None, description="Full name of the asset")
    invested_amount: Decimal = Field(..., description="Total amount invested")
    quantity: Decimal = Field(..., description="Quantity of asset purchased")
    purchase_price: Decimal = Field(..., description="Price per unit at purchase")
    currency: CurrencyEnum = Field(..., description="Currency of the investment")
    
    # External IDs
    coingecko_id: Optional[str] = Field(None, description="CoinGecko API ID")
    twelvedata_id: Optional[str] = Field(None, description="TwelveData API ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Status
    status: InvestmentStatus = Field(
        default=InvestmentStatus.active,
        description="Investment status"
    )

class Investment(InvestmentInDBBase):
    """Complete investment model for internal use"""
    pass

class InvestmentOut(InvestmentInDBBase):
    """Investment model for API responses"""
    
    # Computed fields for responses
    current_value: Optional[Decimal] = Field(
        None,
        description="Current value based on latest price"
    )
    
    gain_loss: Optional[Decimal] = Field(
        None,
        description="Current gain/loss amount"
    )
    
    roi_percentage: Optional[Decimal] = Field(
        None,
        description="Return on investment percentage"
    )
    
    class Config:
        json_encoders = {Decimal: clean_decimal}



class InvestmentCreateResponse(InvestmentOut):
    """Response schema with user-friendly context"""
    holding_context: str = Field(..., description="Context of the holding: 'new_holding' or 'added_to_existing'")
    existing_holdings_count: int = Field(..., description="Number of existing holdings for this symbol")
    total_invested_in_asset: Decimal = Field(..., description="Total invested in this asset across all holdings")
    average_price: Optional[Decimal] = Field(None, description="Average purchase price across all holdings")
    message: str = Field(..., description="User-friendly message")

class AggregatedHolding(BaseModel):
    """Schema for aggregated holdings by symbol"""
    symbol: str
    asset_name: str
    asset_type: AssetType
    total_quantity: Decimal
    total_invested: Decimal
    average_price: Decimal
    current_price: Decimal
    current_value: Decimal
    gain_loss: Decimal
    roi_percentage: Decimal
    purchase_count: int
    currency: str
    purchases: List[Dict[str, Any]]

    model_config = ConfigDict(
        json_encoders={Decimal: clean_decimal}
    )

class AggregatedHoldingsResponse(BaseModel):
    """Response for aggregated holdings endpoint"""
    aggregated_holdings: Dict[str, AggregatedHolding]
    total_symbols: int
    calculation_date: datetime

# PORTFOLIO SUMMARY MODELS
class AssetAllocation(BaseModel):
    """Asset allocation data"""
    asset_type: str
    total_invested: Decimal
    total_value: Decimal
    allocation_percentage: Decimal
    count: int
    
    model_config = ConfigDict(
        json_encoders={Decimal: clean_decimal}
    )

class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics"""
    best_performer: Optional[str]
    best_roi: Decimal
    worst_performer: Optional[str]
    worst_roi: Decimal
    total_assets: int
    profitable_assets: int
    losing_assets: int
    
    model_config = ConfigDict(
        json_encoders={Decimal: clean_decimal}
    )

class PortfolioSummary(BaseModel):
    """Complete portfolio summary"""
    total_invested: Decimal
    current_value: Decimal
    total_gain_loss: Decimal
    total_roi_percentage: Decimal
    items: List[Dict[str, Any]]
    aggregated_holdings: Dict[str, AggregatedHolding]  # NUEVO
    asset_allocation: Dict[str, AssetAllocation]
    performance_metrics: PerformanceMetrics
    
    model_config = ConfigDict(
        json_encoders={Decimal: clean_decimal}
    )


# Export all models
__all__ = [
    'AssetType',
    'CurrencyEnum',
    'InvestmentStatus',
    'InvestmentBase',
    'InvestmentCreate',
    'InvestmentUpdate',
    'Investment',
    'InvestmentOut',
    'InvestmentCreateResponse',  
    'AggregatedHolding',         
    'AggregatedHoldingsResponse',
    'PortfolioSummary',
    'AssetAllocation',
    'PerformanceMetrics',
    'clean_decimal'
]