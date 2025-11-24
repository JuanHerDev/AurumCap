from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import logging

from fastapi import HTTPException, status

from app.models.investment import Investment
from app.models.platform import Platform
from app.schemas.investment import AssetType, CurrencyEnum, InvestmentUpdate

logger = logging.getLogger(__name__)

# CONSTANTS
SYMBOL_REGEX = re.compile(r"^[A-Za-z0-9\.\-\_]{1,64}$")
PROTECTED_FIELDS = {"id", "user_id", "created_at", "updated_at"}
PRICE_TOLERANCE = Decimal('0.01')  # 1% tolerance for inconsistencies in price calculations

class InvestmentCRUDError(Exception):
    """Custom exception for investment CRUD operations"""
    pass

class ValidationError(InvestmentCRUDError):
    """Validation error for investment data"""
    pass

class PlatformCRUD:
    """Platform CRUD operations"""
    
    @staticmethod
    def create_platform(
        db: Session, 
        name: str, 
        platform_type: Optional[str] = None, 
        description: Optional[str] = None
    ) -> Platform:
        """
        Create a new platform with validation
        """
        try:
            if not name or not name.strip():
                raise ValidationError("Platform name cannot be empty")
                
            platform = Platform(
                name=name.strip(),
                type=(platform_type or "other").strip().lower(),
                description=description,
            )
            db.add(platform)
            db.commit()
            db.refresh(platform)
            
            logger.info(f"Platform created: {platform.id} - {platform.name}")
            return platform
            
        except IntegrityError:
            db.rollback()
            logger.error(f"Platform already exists: {name}")
            raise ValidationError(f"Platform '{name}' already exists")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating platform: {e}")
            raise InvestmentCRUDError("Failed to create platform")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating platform: {e}")
            raise InvestmentCRUDError("Unexpected error creating platform")

    @staticmethod
    def get_platform(db: Session, platform_id: int) -> Optional[Platform]:
        """
        Get platform by ID
        """
        try:
            return db.query(Platform).filter(Platform.id == platform_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching platform {platform_id}: {e}")
            return None

class InvestmentCRUD:
    """Investment CRUD operations con created_at como fecha de adquisición"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """
        Validate and normalize symbol format
        """
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol must be a non-empty string")
            
        symbol = symbol.strip()
        if not SYMBOL_REGEX.fullmatch(symbol):
            raise ValidationError(
                "Invalid symbol format. Only letters, numbers, dots, hyphens, and underscores are allowed"
            )
            
        return symbol.upper()

    @staticmethod
    def validate_platform(db: Session, platform_id: Optional[int]) -> None:
        """
        Validate platform exists
        """
        if platform_id is not None:
            platform = PlatformCRUD.get_platform(db, platform_id)
            if not platform:
                raise ValidationError(f"Platform with ID {platform_id} does not exist")

    @staticmethod
    def calculate_purchase_price(
        invested_amount: Decimal, 
        quantity: Decimal
    ) -> Decimal:
        """
        Calculate purchase price from invested amount and quantity
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
            
        purchase_price = invested_amount / quantity
        return purchase_price.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

    @staticmethod
    def validate_and_calculate_purchase_price(
        invested_amount: Decimal,
        quantity: Decimal,
        provided_purchase_price: Optional[Decimal] = None
    ) -> Decimal:
        """
        Validate purchase price consistency and calculate if necessary
        Returns the corrected purchase price
        """
        # Calculate purchase price based on invested amount and quantity
        calculated_price = InvestmentCRUD.calculate_purchase_price(invested_amount, quantity)
        
        # If no price provided, use calculated
        if provided_purchase_price is None:
            return calculated_price
        
        # If price provided, check for consistency
        if provided_purchase_price > 0:
            # Calculate difference percentage
            if calculated_price > 0:
                price_difference = abs(calculated_price - provided_purchase_price)
                price_difference_percentage = price_difference / provided_purchase_price
                
                # If difference exceeds tolerance, log warning and use calculated price
                if price_difference_percentage > PRICE_TOLERANCE:
                    logger.warning(
                        f"Purchase price inconsistency detected: "
                        f"provided={provided_purchase_price}, "
                        f"calculated={calculated_price:.6f}, "
                        f"difference={price_difference_percentage:.2%}"
                    )
                    return calculated_price
            
            # If difference within tolerance, use provided price
            return provided_purchase_price
        
        # If provided price is zero or negative, log warning and use calculated price
        logger.warning(f"Invalid provided purchase price: {provided_purchase_price}. Using calculated price.")
        return calculated_price

    @staticmethod
    def create_investment(db: Session, user_id: int, data) -> Investment:
        """
        Create a new investment - CON VALIDACIÓN MEJORADA DE PRECIO
        """
        try:
            # Validate symbol
            symbol = InvestmentCRUD.validate_symbol(data.symbol)
            
            # Validate platform
            InvestmentCRUD.validate_platform(db, data.platform_id)
            
            # Validate financial data
            if data.invested_amount <= 0:
                raise ValidationError("Invested amount must be greater than zero")
                
            if data.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Convertir a Decimal para cálculos precisos
            invested_amount = Decimal(str(data.invested_amount))
            quantity = Decimal(str(data.quantity))
            provided_purchase_price = (
                Decimal(str(data.purchase_price)) 
                if data.purchase_price is not None 
                else None
            )

            # Validate and calculate purchase price
            purchase_price = InvestmentCRUD.validate_and_calculate_purchase_price(
                invested_amount=invested_amount,
                quantity=quantity,
                provided_purchase_price=provided_purchase_price
            )

            # Validate final purchase price
            if purchase_price <= 0:
                raise ValidationError("Calculated purchase price must be greater than zero")

            # Debugging log
            if provided_purchase_price is not None and provided_purchase_price != purchase_price:
                logger.info(
                    f"Purchase price corrected for user {user_id}: "
                    f"from {provided_purchase_price} to {purchase_price:.6f}"
                )

            investment = Investment(
                user_id=user_id,
                platform_id=data.platform_id,
                symbol=symbol,
                asset_name=data.asset_name,
                asset_type=data.asset_type,
                invested_amount=invested_amount,
                quantity=quantity,
                purchase_price=purchase_price,
                currency=data.currency,
                coingecko_id=data.coingecko_id,
                twelvedata_id=data.twelvedata_id,
                notes=getattr(data, 'notes', None),
            )

            db.add(investment)
            db.commit()
            db.refresh(investment)
            
            logger.info(f"Investment created: {investment.id} for user {user_id}")
            return investment

        except ValidationError:
            db.rollback()
            raise
        except IntegrityError:
            db.rollback()
            logger.error(f"Integrity error creating investment for user {user_id}")
            raise ValidationError("Investment data violates integrity constraints")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating investment for user {user_id}: {e}")
            raise InvestmentCRUDError("Failed to create investment due to database error")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating investment for user {user_id}: {e}")
            raise InvestmentCRUDError("Unexpected error creating investment")

    @staticmethod
    def get_investment(db: Session, inv_id: int, user_id: int) -> Optional[Investment]:
        """
        Get investment by ID with user ownership check
        """
        try:
            return (
                db.query(Investment)
                .filter(Investment.id == inv_id, Investment.user_id == user_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching investment {inv_id}: {e}")
            return None

    @staticmethod
    def list_investments(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        asset_type: Optional[str] = None
    ) -> List[Investment]:
        """
        List investments with filtering and pagination
        """
        try:
            query = db.query(Investment).filter(Investment.user_id == user_id)
            
            if asset_type:
                query = query.filter(Investment.asset_type == asset_type)
                
            return (
                query
                .order_by(Investment.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error listing investments for user {user_id}: {e}")
            return []

    @staticmethod
    def update_investment(
        db: Session, 
        inv: Investment, 
        update_data: Dict[str, Any]
    ) -> Investment:
        """
        Update investment with validation and protection - CON VALIDACIÓN MEJORADA DE PRECIO
        """
        try:
            # Validate update data
            validated = InvestmentUpdate(**update_data)
            updates = validated.model_dump(exclude_unset=True)

            # Apply updates with validation
            for field, value in updates.items():
                if field in PROTECTED_FIELDS:
                    logger.warning(f"Attempted to update protected field: {field}")
                    continue

                # Special validation for symbol
                if field == "symbol":
                    value = InvestmentCRUD.validate_symbol(value)

                # Special validation for platform_id
                if field == "platform_id":
                    InvestmentCRUD.validate_platform(db, value)

                # Validar montos financieros
                if field in ["invested_amount", "quantity"] and value is not None:
                    if value <= 0:
                        raise ValidationError(f"{field} must be greater than zero")

                setattr(inv, field, value)

            # Recalculate purchase price if relevant fields changed
            if "invested_amount" in updates or "quantity" in updates or "purchase_price" in updates:
                # Get current values
                current_invested_amount = Decimal(str(inv.invested_amount))
                current_quantity = Decimal(str(inv.quantity))
                current_purchase_price = (
                    Decimal(str(inv.purchase_price)) 
                    if inv.purchase_price is not None 
                    else None
                )
                
                # Recalculate purchase price if needed
                if "purchase_price" not in updates:
                    new_purchase_price = InvestmentCRUD.validate_and_calculate_purchase_price(
                        invested_amount=current_invested_amount,
                        quantity=current_quantity,
                        provided_purchase_price=current_purchase_price
                    )
                    inv.purchase_price = new_purchase_price
                else:
                    # Validate provided purchase price
                    provided_price = Decimal(str(updates["purchase_price"]))
                    validated_price = InvestmentCRUD.validate_and_calculate_purchase_price(
                        invested_amount=current_invested_amount,
                        quantity=current_quantity,
                        provided_purchase_price=provided_price
                    )
                    inv.purchase_price = validated_price

            inv.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(inv)
            
            logger.info(f"Investment updated: {inv.id}")
            return inv

        except ValidationError:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error updating investment {inv.id}: {e}")
            raise InvestmentCRUDError("Failed to update investment")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating investment {inv.id}: {e}")
            raise InvestmentCRUDError("Unexpected error updating investment")

    @staticmethod
    def delete_investment(db: Session, inv: Investment, user_id: int) -> None:
        """
        Delete investment with ownership verification
        """
        try:
            # Double-check ownership
            if inv.user_id != user_id:
                logger.warning(f"User {user_id} attempted to delete investment {inv.id} owned by {inv.user_id}")
                raise PermissionError("Not allowed to delete this investment")

            db.delete(inv)
            db.commit()
            logger.info(f"Investment deleted: {inv.id} by user {user_id}")
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error deleting investment {inv.id}: {e}")
            raise InvestmentCRUDError("Failed to delete investment")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error deleting investment {inv.id}: {e}")
            raise InvestmentCRUDError("Unexpected error deleting investment")

    @staticmethod
    def recalculate_all_purchase_prices(db: Session, user_id: int) -> Dict[str, int]:
        """
        Recalcula todos los precios de compra para las inversiones de un usuario
        Útil para corregir datos inconsistentes
        """
        try:
            investments = db.query(Investment).filter(Investment.user_id == user_id).all()
            corrected_count = 0
            
            for inv in investments:
                original_price = inv.purchase_price
                new_price = InvestmentCRUD.validate_and_calculate_purchase_price(
                    invested_amount=Decimal(str(inv.invested_amount)),
                    quantity=Decimal(str(inv.quantity)),
                    provided_purchase_price=Decimal(str(inv.purchase_price))
                )
                
                if new_price != original_price:
                    inv.purchase_price = new_price
                    corrected_count += 1
                    logger.info(
                        f"Corrected purchase price for investment {inv.id}: "
                        f"from {original_price} to {new_price:.6f}"
                    )
            
            if corrected_count > 0:
                db.commit()
            
            return {
                "total_investments": len(investments),
                "corrected_prices": corrected_count
            }
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error recalculating prices for user {user_id}: {e}")
            raise InvestmentCRUDError("Failed to recalculate purchase prices")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error recalculating prices for user {user_id}: {e}")
            raise InvestmentCRUDError("Unexpected error recalculating purchase prices")

# Backward compatibility functions
def create_platform(db: Session, name: str, type: Optional[str] = None, description: Optional[str] = None) -> Platform:
    return PlatformCRUD.create_platform(db, name, type, description)

def get_platform(db: Session, platform_id: int) -> Optional[Platform]:
    return PlatformCRUD.get_platform(db, platform_id)

def validate_symbol(symbol: str):
    return InvestmentCRUD.validate_symbol(symbol)

def create_investment(db: Session, user_id: int, data) -> Investment:
    return InvestmentCRUD.create_investment(db, user_id, data)

def get_investment(db: Session, inv_id: int, user_id: int) -> Optional[Investment]:
    return InvestmentCRUD.get_investment(db, inv_id, user_id)

def list_investments(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    asset_type: Optional[str] = None
) -> List[Investment]:
    return InvestmentCRUD.list_investments(db, user_id, skip, limit, asset_type)

def update_investment(db: Session, inv: Investment, update_data: Dict) -> Investment:
    return InvestmentCRUD.update_investment(db, inv, update_data)

def delete_investment(db: Session, inv: Investment, user_id: int):
    return InvestmentCRUD.delete_investment(db, inv, user_id)

def recalculate_all_purchase_prices(db: Session, user_id: int) -> Dict[str, int]:
    return InvestmentCRUD.recalculate_all_purchase_prices(db, user_id)