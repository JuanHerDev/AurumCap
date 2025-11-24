from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.db.database import get_db
from app.schemas.platform import PlatformCreate, PlatformOut, PlatformUpdate, PlatformWithStats, PlatformType
from app.crud.investment import create_platform, get_platform, InvestmentCRUDError, ValidationError
from app.deps.auth import get_current_user, get_current_active_admin
from app.models.user import User
from app.models.platform import Platform
from app.models.investment import Investment

router = APIRouter(
    prefix="/platforms",
    tags=["platforms"]
)

@router.post(
    "",
    response_model=PlatformOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Platform",
    description="Create a new investment platform (Admin only)"
)
def create_platform_endpoint(
    payload: PlatformCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Create a new investment platform - ADMIN ONLY
    """
    try:

        platform = create_platform(
            db, 
            payload.name, 
            payload.type,
            payload.description
        )
        return platform
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvestmentCRUDError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get(
    "",
    response_model=List[PlatformOut],
    summary="List Platforms", 
    description="Get list of all investment platforms"
)
def list_platforms(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    type: Optional[PlatformType] = Query(None, description="Filter by platform type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all investment platforms
    """
    try:
        query = db.query(Platform)
        
        if type:
            query = query.filter(Platform.type == type)
            
        platforms = query.order_by(Platform.name).offset(skip).limit(limit).all()
        return platforms
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving platforms"
        )

@router.get(
    "/stats",
    response_model=List[PlatformWithStats],
    summary="Get Platforms with Stats",
    description="Get platforms with investment statistics (Admin only)"
)
def get_platforms_with_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Get platforms with investment statistics - ADMIN ONLY
    """
    try:
        platforms = db.query(Platform).all()
        result = []
        
        for platform in platforms:
            # Count investments for this platform
            investment_count = db.query(Investment).filter(
                Investment.platform_id == platform.id
            ).count()
            
            # Calculate total invested
            total_invested_result = db.query(Investment).filter(
                Investment.platform_id == platform.id
            ).with_entities(
                db.func.sum(Investment.invested_amount)
            ).scalar()
            
            total_invested = Decimal(str(total_invested_result)) if total_invested_result else Decimal('0')
            
            platform_data = PlatformWithStats(
                id=platform.id,
                name=platform.name,
                type=platform.type,
                description=platform.description,
                created_at=platform.created_at,
                updated_at=platform.updated_at,
                investment_count=investment_count,
                total_invested=total_invested
            )
            result.append(platform_data)
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving platform statistics"
        )

@router.get(
    "/{platform_id}",
    response_model=PlatformOut,
    summary="Get Platform",
    description="Get specific platform by ID"
)
def get_platform_endpoint(
    platform_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific platform
    """
    platform = get_platform(db, platform_id)
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found"
        )
    return platform

@router.put(
    "/{platform_id}",
    response_model=PlatformOut,
    summary="Update Platform", 
    description="Update a platform (Admin only)"
)
def update_platform(
    platform_id: int,
    payload: PlatformUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Update a platform - ADMIN ONLY
    """
    try:
        platform = get_platform(db, platform_id)
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform not found"
            )
        
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(platform, field, value)
            
        db.commit()
        db.refresh(platform)
        return platform
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating platform"
        )

@router.delete(
    "/{platform_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Platform",
    description="Delete a platform (Admin only)"
)
def delete_platform(
    platform_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Delete a platform - ADMIN ONLY
    """
    try:
        platform = get_platform(db, platform_id)
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform not found"
            )
        
        # Check if platform has investments
        investment_count = db.query(Investment).filter(
            Investment.platform_id == platform_id
        ).count()
        
        if investment_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete platform with {investment_count} investments. Update investments first."
            )
        
        db.delete(platform)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting platform"
        )

@router.post("/seed-defaults")
def seed_default_platforms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Seed default platforms - ADMIN ONLY
    """
    try:
        default_platforms = [
            {
                "name": "Binance",
                "type": PlatformType.exchange,
                "description": "Global cryptocurrency exchange"
            },
            {
                "name": "Coinbase", 
                "type": PlatformType.exchange,
                "description": "US-based cryptocurrency exchange"
            },
            {
                "name": "Interactive Brokers",
                "type": PlatformType.broker,
                "description": "International brokerage platform"
            },
            {
                "name": "eToro",
                "type": PlatformType.broker, 
                "description": "Social trading and investment platform"
            },
            {
                "name": "Metamask",
                "type": PlatformType.wallet,
                "description": "Cryptocurrency wallet and DeFi gateway"
            },
            {
                "name": "Ledger",
                "type": PlatformType.wallet,
                "description": "Hardware cryptocurrency wallet"
            },
            {
                "name": "Local Bitcoins",
                "type": PlatformType.exchange,
                "description": "Peer-to-peer Bitcoin trading platform"
            },
            {
                "name": "Hapi",
                "type": PlatformType.broker,
                "description": "Brokerage platform for stocks and crypto"
            },
            {
                "name": "Other",
                "type": PlatformType.other, 
                "description": "Other platform or manual entry"
            }
        ]
        
        created_platforms = []
        for platform_data in default_platforms:
            # Check if platform already exists
            existing = db.query(Platform).filter(
                Platform.name == platform_data["name"]
            ).first()
            
            if not existing:
                platform = Platform(**platform_data)
                db.add(platform)
                created_platforms.append(platform_data["name"])
        
        db.commit()
        
        return {
            "message": f"Created {len(created_platforms)} default platforms",
            "created_platforms": created_platforms
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error seeding platforms: {str(e)}"
        )