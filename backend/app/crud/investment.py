from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
from typing import Optional, List, Dict
from datetime import datetime, timezone
import re

from app.models.investment import Investment
from app.models.platform import Platform
from app.schemas.investment import AssetType, CurrencyEnum, InvestmentUpdate


# PLATFORM CRUD
def create_platform(db: Session, name: str, type: Optional[str] = None, description: Optional[str] = None) -> Platform:
    try:
        platform = Platform(
            name=name.strip(),
            type=(type or "other").strip().lower(),
            description=description,
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)
        return platform
    except SQLAlchemyError:
        db.rollback()
        raise


def get_platform(db: Session, platform_id: int) -> Optional[Platform]:
    return db.query(Platform).filter(Platform.id == platform_id).first()



# INVESTMENT CRUD

SYMBOL_REGEX = re.compile(r"^[A-Za-z0-9\.\-\_]{1,64}$")


def validate_symbol(symbol: str):
    if not SYMBOL_REGEX.fullmatch(symbol):
        raise ValueError("Invalid symbol format")
    return symbol.upper()


def create_investment(db: Session, user_id: int, data) -> Investment:
    symbol = validate_symbol(data.symbol.strip())

    # Validate platform
    if data.platform_id is not None:
        if not get_platform(db, data.platform_id):
            raise ValueError("Platform does not exist")

    try:
        # AUTO-CALC purchase_price if missing
        purchase_price = data.purchase_price
        if purchase_price is None:
            qty = Decimal(str(data.quantity))
            inv = Decimal(str(data.invested_amount))
            purchase_price = inv / qty if qty != 0 else Decimal("0")

        inv = Investment(
            user_id=user_id,
            platform_id=data.platform_id,
            symbol=symbol,
            asset_name=data.asset_name,
            asset_type=data.asset_type,
            invested_amount=data.invested_amount,
            quantity=data.quantity,
            purchase_price=purchase_price,
            currency=data.currency,
            coingecko_id=data.coingecko_id,
            twelvedata_id=data.twelvedata_id,
            date_acquired=data.date_acquired or datetime.now(timezone.utc),
        )

        db.add(inv)
        db.commit()
        db.refresh(inv)
        return inv

    except SQLAlchemyError:
        db.rollback()
        raise


def get_investment(db: Session, inv_id: int, user_id: int) -> Optional[Investment]:
    return (
        db.query(Investment)
        .filter(Investment.id == inv_id, Investment.user_id == user_id)
        .first()
    )


def list_investments(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Investment]:
    return (
        db.query(Investment)
        .filter(Investment.user_id == user_id)
        .order_by(Investment.date_acquired.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )



# UPDATE

PROTECTED_FIELDS = {"id", "user_id", "created_at", "updated_at"}


def update_investment(db: Session, inv: Investment, update_data: Dict) -> Investment:
    try:
        validated = InvestmentUpdate(**update_data)
        updates = validated.model_dump(exclude_unset=True)

        for field, value in updates.items():

            if field in PROTECTED_FIELDS:
                continue

            # Validate symbol
            if field == "symbol":
                value = validate_symbol(value.strip())

            # Validate platform
            if field == "platform_id":
                if value is not None and not get_platform(db, value):
                    raise ValueError("Platform does not exist")

            setattr(inv, field, value)

        db.commit()
        db.refresh(inv)
        return inv

    except SQLAlchemyError:
        db.rollback()
        raise



# DELETE

def delete_investment(db: Session, inv: Investment, user_id: int):
    # Safety: avoid deleting other people's investments
    if inv.user_id != user_id:
        raise PermissionError("Not allowed to delete this investment")

    try:
        db.delete(inv)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
