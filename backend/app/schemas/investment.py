from pydantic import BaseModel, Field, condecimal, field_validator
from typing import Optional, Annotated
from datetime import datetime
from enum import Enum
from decimal import Decimal


# --------------------------
# DECIMAL SERIALIZER
# --------------------------
def clean_decimal(v: Decimal):
    if v is None:
        return None
    try:
        return format(v.normalize(), 'f')
    except:
        return str(v)


# ENUMS
class AssetType(str, Enum):
    crypto = "crypto"
    stock = "stock"
    other = "other"


class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    COP = "COP"


# FIELD TYPES
SymbolStr = Annotated[str, Field(min_length=1, max_length=64, strip_whitespace=True)]
AssetNameStr = Annotated[str, Field(max_length=255)]

MoneyDecimal = condecimal(max_digits=18, decimal_places=6)
QuantityDecimal = condecimal(max_digits=28, decimal_places=10)


# --------------------------
# BASE MODEL
# --------------------------
class InvestmentBase(BaseModel):
    asset_type: AssetType = Field(default=AssetType.other, alias="type")

    symbol: SymbolStr
    asset_name: Optional[AssetNameStr] = None

    invested_amount: Decimal
    quantity: Decimal

    purchase_price: Optional[Decimal] = None
    currency: CurrencyEnum = CurrencyEnum.USD
    date_acquired: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {Decimal: clean_decimal}
    }

    @field_validator("invested_amount", "quantity", "purchase_price", mode="before")
    def convert_decimal(cls, v):
        if v is None:
            return None
        return Decimal(str(v))


# --------------------------
# CREATE MODEL
# --------------------------
class InvestmentCreate(InvestmentBase):
    coingecko_id: Optional[str] = None
    twelvedata_id: Optional[str] = None
    platform_id: Optional[int] = None  # tests do NOT send platform_id


# --------------------------
# UPDATE MODEL
# --------------------------
class InvestmentUpdate(BaseModel):
    symbol: Optional[str] = None
    asset_name: Optional[AssetNameStr] = None
    invested_amount: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None
    currency: Optional[CurrencyEnum] = None
    date_acquired: Optional[datetime] = None

    asset_type: Optional[AssetType] = Field(default=None, alias="type")
    platform_id: Optional[int] = None

    model_config = {
        "populate_by_name": True
    }

    @field_validator("invested_amount", "quantity", "purchase_price", mode="before")
    def convert_decimal(cls, v):
        if v is None:
            return None
        return Decimal(str(v))


# --------------------------
# DB MODELS
# --------------------------
class InvestmentInDBBase(InvestmentBase):
    id: int
    user_id: int
    platform_id: Optional[int] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "json_encoders": {Decimal: clean_decimal}
    }


class Investment(InvestmentInDBBase):
    pass


class InvestmentOut(InvestmentInDBBase):
    pass
