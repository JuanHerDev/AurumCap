from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from decimal import Decimal
from app.models.investment import Investment
from app.models.platform import Platform
from app.schemas.investment import InvestmentCreate, InvestmentUpdate

class InvestmentCRUDError(Exception):
    pass

class ValidationError(Exception):
    pass

# Platform CRUD functions

def get_platform(db: Session, platform_id: int) -> Optional[Platform]:
    """Get platform by ID"""
    return db.query(Platform).filter(Platform.id == platform_id).first()

def get_platforms_by_asset_type(db: Session, asset_type: str, skip: int = 0, limit: int = 100) -> List[Platform]:
    """Get active platforms that support a specific asset type"""
    return db.query(Platform).filter(
        Platform.is_active == True,
        Platform.supported_asset_types.contains([asset_type])
    ).offset(skip).limit(limit).all()

def get_active_platforms(db: Session, skip: int = 0, limit: int = 100) -> List[Platform]:
    """Get all active platforms"""
    return db.query(Platform).filter(Platform.is_active == True).offset(skip).limit(limit).all()

def create_platform(
    db: Session, 
    name: str, 
    display_name: str, 
    platform_type: str, 
    description: Optional[str] = None,
    supported_asset_types: Optional[List[str]] = None, 
    api_config: Optional[Dict] = None, 
    icon: Optional[str] = None
) -> Platform:
    """Create a new platform (admin only)"""
    
    # Verify if platform exists
    existing = db.query(Platform).filter(Platform.name == name).first()
    if existing:
        raise ValidationError(f"Platform with name '{name}' already exists")
    
    platform = Platform(
        name=name,
        display_name=display_name,
        type=platform_type,
        description=description,
        supported_asset_types=supported_asset_types or [],
        api_config=api_config or {},
        icon=icon
    )
    
    try:
        db.add(platform)
        db.commit()
        db.refresh(platform)
        return platform
    except Exception as e:
        db.rollback()
        raise InvestmentCRUDError(f"Error creating platform: {str(e)}")

# Investment CRUD functions

def create_investment(db: Session, user_id: int, payload: InvestmentCreate) -> Investment:
    """Create a new investment with platform validation"""
    try:
        # Validate platform if provided
        if payload.platform_id:
            platform = get_platform(db, payload.platform_id)
            if not platform:
                raise ValidationError("Invalid platform ID")
            
            # Validate asset type compatibility
            if (platform.supported_asset_types and 
                payload.asset_type.value not in platform.supported_asset_types):
                raise ValidationError(
                    f"Platform '{platform.display_name}' does not support asset type '{payload.asset_type.value}'"
                )

        # Create investment
        investment = Investment(
            user_id=user_id,
            platform_id=payload.platform_id,
            platform_specific_id=payload.platform_specific_id,
            asset_type=payload.asset_type,
            symbol=payload.symbol.upper(),
            asset_name=payload.asset_name,
            coingecko_id=payload.coingecko_id,
            twelvedata_id=payload.twelvedata_id,
            invested_amount=payload.invested_amount,
            quantity=payload.quantity,
            purchase_price=payload.purchase_price,
            currency=payload.currency,
            notes=payload.notes
        )
        
        db.add(investment)
        db.commit()
        db.refresh(investment)
        return investment
        
    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        raise InvestmentCRUDError(f"Error creating investment: {str(e)}")

def get_investment(db: Session, investment_id: int, user_id: int) -> Optional[Investment]:
    """Get investment by ID for a specific user"""
    return db.query(Investment).filter(
        and_(Investment.id == investment_id, Investment.user_id == user_id)
    ).first()

def list_investments(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    asset_type: Optional[str] = None
) -> List[Investment]:
    """List investments for a user with optional asset type filtering"""
    query = db.query(Investment).filter(Investment.user_id == user_id)
    
    if asset_type:
        query = query.filter(Investment.asset_type == asset_type)
        
    return query.order_by(Investment.created_at.desc()).offset(skip).limit(limit).all()

def update_investment(db: Session, investment: Investment, update_data: Dict[str, Any]) -> Investment:
    """Update an existing investment with platform validation"""
    try:
        # Validate platform if being updated
        if 'platform_id' in update_data and update_data['platform_id']:
            platform = get_platform(db, update_data['platform_id'])
            if not platform:
                raise ValidationError("Invalid platform ID")
            
            # Validate asset type compatibility
            if (platform.supported_asset_types and 
                investment.asset_type.value not in platform.supported_asset_types):
                raise ValidationError(
                    f"Platform '{platform.display_name}' does not support asset type '{investment.asset_type.value}'"
                )

        for field, value in update_data.items():
            setattr(investment, field, value)
            
        db.commit()
        db.refresh(investment)
        return investment
        
    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        raise InvestmentCRUDError(f"Error updating investment: {str(e)}")

def delete_investment(db: Session, investment: Investment, user_id: int) -> None:
    """Delete an investment if it belongs to the user"""
    try:
        if investment.user_id != user_id:
            raise PermissionError("Not authorized to delete this investment")
            
        db.delete(investment)
        db.commit()
        
    except PermissionError:
        raise
    except Exception as e:
        db.rollback()
        raise InvestmentCRUDError(f"Error deleting investment: {str(e)}")

def get_user_investments_by_symbol(db: Session, user_id: int, symbol: str) -> List[Investment]:
    """Get all investments for a user by symbol"""
    return db.query(Investment).filter(
        and_(
            Investment.user_id == user_id,
            Investment.symbol == symbol.upper()
        )
    ).all()

def get_platforms_by_asset_type(db: Session, asset_type: str, skip: int = 0, limit: int = 100) -> List[Platform]:
    """Obtener plataformas que soportan un tipo de activo específico"""
    return db.query(Platform).filter(
        Platform.is_active == True,
        Platform.supported_asset_types.contains([asset_type])
    ).offset(skip).limit(limit).all()

def get_existing_investment(db: Session, user_id: int, symbol: str, platform_id: int = None):
    """
    Find existing investment for the same symbol and platform
    """
    query = db.query(Investment).filter(
        Investment.user_id == user_id,
        Investment.symbol == symbol
    )
    
    if platform_id:
        query = query.filter(Investment.platform_id == platform_id)
    
    return query.first()

def update_investment_quantity(db: Session, investment: Investment, additional_quantity: Decimal, additional_invested: Decimal):
    """
    Update existing investment with additional quantity and investment
    """
    investment.quantity = Decimal(str(investment.quantity)) + additional_quantity
    investment.invested_amount = Decimal(str(investment.invested_amount)) + additional_invested
    
    # Recalculate average purchase price
    if investment.quantity > 0:
        investment.purchase_price = investment.invested_amount / investment.quantity
    
    investment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(investment)
    return investment