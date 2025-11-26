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
    
    # Specific platform asset ID
    platform_specific_id: Optional[str] = Field(
        None,
        max_length=255,
        description="ID específico del activo en la plataforma"
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

    investment_strategy: Optional[str] = Field(
        None,
        max_length=100,
        description="Investment strategy or notes"
    )

    transaction_date: Optional[datetime] = Field(
        None,
        description="Date of the investment transaction (if its different from creation date)"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the investment"
    )

    @field_validator('platform_id', mode='before')
    @classmethod
    def validate_platform_id(cls, v):
        """Validate and convert platform_id"""
        if v is None or v == '':
            return None
        
        try:
            # If string, convert to int
            if isinstance(v, str):
                return int(v)
            # If already int, validate
            elif isinstance(v, int):
                if v < 1:
                    raise ValueError('Platform ID must be positive')
                return v
            else:
                raise ValueError(f"Unsupported type for platform_id: {type(v)}")
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid platform_id value '{v}': {e}")
            return None

    @field_validator('coingecko_id', 'twelvedata_id', 'platform_specific_id', mode='before')
    @classmethod
    def validate_api_ids(cls, v):
        """Validate API IDs"""
        if v is not None and not isinstance(v, str):
            raise ValueError('API ID must be a string')
        return v

# UPDATE MODEL
class InvestmentUpdate(BaseModel):
    """Schema for updating investments (partial updates)"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_encoders={Decimal: clean_decimal},
        validate_assignment=True,
        extra='ignore'  # Permitir campos extra del frontend
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
    
    # Specific platform asset ID
    platform_specific_id: Optional[str] = Field(
        None,
        max_length=255,
        description="ID específico del activo en la plataforma"
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

    investment_strategy: Optional[str] = Field(
        None,
        max_length=100,
        description="Investment strategy used"
    )

    transaction_date: Optional[datetime] = Field(
        None,
        description="Date of the investment transaction"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the investment"
    )

    # Campos de alias para compatibilidad con frontend
    platform: Optional[str] = Field(None, description="Alias for platform_id (frontend compatibility)")
    strategy: Optional[str] = Field(None, description="Alias for investment_strategy (frontend compatibility)")

    @model_validator(mode='before')
    @classmethod
    def map_frontend_fields(cls, data):
        """Map frontend field names to backend field names and convert types"""
        if isinstance(data, dict):
            # Mapear 'platform' -> 'platform_id' y convertir a int
            if 'platform' in data:
                platform_value = data['platform']
                if platform_value is not None and platform_value != '':
                    try:
                        # Convertir string a int
                        data['platform_id'] = int(platform_value)
                        logger.info(f"🔧 Mapped 'platform' to 'platform_id': {data['platform_id']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Could not convert platform value '{platform_value}' to int: {e}")
                        # Si no se puede convertir, establecer como None
                        data['platform_id'] = None
                else:
                    data['platform_id'] = None
            
            # Mapear 'strategy' -> 'investment_strategy'  
            if 'strategy' in data and 'investment_strategy' not in data:
                data['investment_strategy'] = data['strategy']
                logger.info(f"🔧 Mapped 'strategy' to 'investment_strategy': {data['investment_strategy']}")
            
            # También manejar platform_id directamente si viene como string
            if 'platform_id' in data and isinstance(data['platform_id'], str):
                platform_id_value = data['platform_id']
                if platform_id_value and platform_id_value != '':
                    try:
                        data['platform_id'] = int(platform_id_value)
                        logger.info(f"🔧 Converted platform_id from string to int: {data['platform_id']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Could not convert platform_id value '{platform_id_value}' to int: {e}")
                        data['platform_id'] = None
                else:
                    data['platform_id'] = None
            
            # Remover campos mapeados para evitar duplicados
            data.pop('platform', None)
            data.pop('strategy', None)
        
        return data

    # Validadores mejorados para manejar conversiones
    @field_validator('platform_id', mode='before')
    @classmethod
    def validate_platform_id(cls, v):
        """Validate and convert platform_id"""
        if v is None or v == '':
            return None
            
        try:
            # Si es string, convertir a int
            if isinstance(v, str):
                return int(v)
            # Si ya es int, validar
            elif isinstance(v, int):
                if v < 1:
                    raise ValueError('Platform ID must be positive')
                return v
            else:
                raise ValueError(f"Unsupported type for platform_id: {type(v)}")
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid platform_id value '{v}': {e}")
            return None

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

    @field_validator('coingecko_id', 'twelvedata_id', 'platform_specific_id', mode='before')
    @classmethod
    def validate_api_ids(cls, v):
        """Validate API IDs"""
        if v is not None and not isinstance(v, str):
            raise ValueError('API ID must be a string')
        return v

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
    
    # Specific platform asset ID
    platform_specific_id: Optional[str] = Field(
        None, 
        description="ID específico del activo en la plataforma"
    )
    
    # Core investment fields
    asset_type: AssetType = Field(..., description="Type of asset")
    symbol: str = Field(..., description="Asset symbol/ticker")
    asset_name: Optional[str] = Field(None, description="Full name of the asset")
    invested_amount: Decimal = Field(..., description="Total amount invested")
    quantity: Decimal = Field(..., description="Quantity of asset purchased")
    purchase_price: Decimal = Field(..., description="Price per unit at purchase")
    currency: CurrencyEnum = Field(..., description="Currency of the investment")
    
    # Nuevos campos
    investment_strategy: Optional[str] = Field(None, description="Investment strategy")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date")
    
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
    
    model_config = ConfigDict(
        json_encoders={Decimal: clean_decimal}
    )

class InvestmentCreateResponse(InvestmentOut):
    """Response schema with user-friendly context"""
    holding_context: str = Field(..., description="Context of the holding: 'new_holding' or 'added_to_existing'")
    existing_holdings_count: int = Field(..., description="Number of existing holdings for this symbol")
    total_invested_in_asset: Decimal = Field(..., description="Total invested in this asset across all holdings")
    average_price: Optional[Decimal] = Field(None, description="Average purchase price across all holdings")
    message: str = Field(..., description="User-friendly message")

class InvestmentErrorResponse(BaseModel):
    """Error response schema for investment operations"""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    symbol: Optional[str] = Field(None, description="Related symbol")
    holding_context: Optional[str] = Field(None, description="Holding context at time of error")

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
    aggregated_holdings: Dict[str, AggregatedHolding]
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