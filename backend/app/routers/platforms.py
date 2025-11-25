from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.db.database import get_db
from app.schemas.platform import PlatformCreate, PlatformOut, PlatformUpdate, PlatformWithStats, PlatformType
from app.crud.investment import create_platform, get_platform, get_platforms_by_asset_type, get_active_platforms, InvestmentCRUDError, ValidationError
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
            payload.display_name,
            payload.type,
            payload.description,
            payload.supported_asset_types,
            payload.api_config,
            payload.icon
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
    asset_type: Optional[str] = Query(None, description="Filter by supported asset type"),
    active_only: bool = Query(True, description="Return only active platforms"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all investment platforms with filtering
    """
    try:
        query = db.query(Platform)
        
        if active_only:
            query = query.filter(Platform.is_active == True)
            
        if type:
            query = query.filter(Platform.type == type)
            
        if asset_type:
            # CORREGIDO: Usar funciones JSON de PostgreSQL
            from sqlalchemy import text
            query = query.filter(
                text(f"platforms.supported_asset_types::jsonb @> '\"{asset_type}\"'::jsonb")
            )
            
        platforms = query.order_by(Platform.display_name).offset(skip).limit(limit).all()
        return platforms
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving platforms"
        )

@router.get(
    "/by-asset-type/{asset_type}",
    response_model=List[PlatformOut],
    summary="Get Platforms by Asset Type",
    description="Get platforms that support a specific asset type",
    operation_id="get_platforms_by_asset_type"
)
def get_platforms_by_asset_type(
    asset_type: str,
    active_only: bool = Query(True, description="Return only active platforms"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get platforms that support a specific asset type
    """
    try:
        print(f"🔍 Buscando plataformas para asset_type: '{asset_type}'")
        
        # Mapeo de asset types del frontend al backend
        asset_type_mapping = {
            "stocks": "stock",  # Frontend usa "stocks", backend usa "stock"
            "crypto": "crypto",
            "etf": "etf", 
            "bond": "bond",
            "real_estate": "real_estate",
            "other": "other"
        }
        
        # Convertir asset_type del frontend al formato del backend
        backend_asset_type = asset_type_mapping.get(asset_type, asset_type)
        print(f"   Asset type convertido: '{backend_asset_type}'")
        
        # Validar que el asset_type es válido
        valid_asset_types = ["stock", "crypto", "etf", "bond", "real_estate", "other"]
        if backend_asset_type not in valid_asset_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid asset type '{asset_type}'. Must be one of: {list(asset_type_mapping.keys())}"
            )
        
        # Obtener plataformas que soportan este tipo de activo
        query = db.query(Platform)
        
        if active_only:
            query = query.filter(Platform.is_active == True)
            
        # CORREGIDO: Usar funciones JSON de PostgreSQL
        # Para JSON arrays, usamos la función jsonb_array_elements_text o el operador @>
        from sqlalchemy import text
        platforms = query.filter(
            text(f"platforms.supported_asset_types::jsonb @> '\"{backend_asset_type}\"'::jsonb")
        ).order_by(Platform.display_name).all()
        
        print(f"✅ Encontradas {len(platforms)} plataformas para '{asset_type}'")
        
        # Debug: mostrar lo que se está devolviendo
        for platform in platforms:
            print(f"   📍 {platform.display_name} - {platform.supported_asset_types}")
        
        return platforms
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en get_platforms_by_asset_type: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving platforms by asset type: {str(e)}"
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
                display_name=platform.display_name,
                type=platform.type,
                description=platform.description,
                is_active=platform.is_active,
                supported_asset_types=platform.supported_asset_types,
                api_config=platform.api_config,
                icon=platform.icon,
                created_at=platform.created_at,
                updated_at=platform.updated_at,
                investment_count=investment_count,
                total_invested=float(total_invested)
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
                "name": "binance",
                "display_name": "Binance",
                "type": PlatformType.exchange,
                "description": "Global cryptocurrency exchange",
                "supported_asset_types": ["crypto"],
                "icon": "binance-icon.png"
            },
            {
                "name": "coinbase",
                "display_name": "Coinbase", 
                "type": PlatformType.exchange,
                "description": "US-based cryptocurrency exchange",
                "supported_asset_types": ["crypto"],
                "icon": "coinbase-icon.png"
            },
            {
                "name": "interactive_brokers",
                "display_name": "Interactive Brokers",
                "type": PlatformType.broker,
                "description": "International brokerage platform",
                "supported_asset_types": ["stock", "etf", "bond"],
                "icon": "ib-icon.png"
            },
            {
                "name": "etoro",
                "display_name": "eToro", 
                "type": PlatformType.broker,
                "description": "Social trading and investment platform",
                "supported_asset_types": ["stock", "crypto", "etf"],
                "icon": "etoro-icon.png"
            },
            {
                "name": "metamask",
                "display_name": "Metamask",
                "type": PlatformType.wallet,
                "description": "Cryptocurrency wallet and DeFi gateway",
                "supported_asset_types": ["crypto"],
                "icon": "metamask-icon.png"
            },
            {
                "name": "ledger",
                "display_name": "Ledger",
                "type": PlatformType.wallet,
                "description": "Hardware cryptocurrency wallet",
                "supported_asset_types": ["crypto"],
                "icon": "ledger-icon.png"
            },
            {
                "name": "other",
                "display_name": "Other", 
                "type": PlatformType.other,
                "description": "Other platform or manual entry",
                "supported_asset_types": ["stock", "crypto", "etf", "bond", "real_estate", "other"],
                "icon": "other-icon.png"
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
                created_platforms.append(platform_data["display_name"])
        
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

@router.get(
    "/debug/all",
    summary="Debug - Get All Platforms",
    description="Debug endpoint to see all platforms and their data"
)
def debug_all_platforms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Debug endpoint to see all platform data
    """
    platforms = db.query(Platform).all()
    
    result = []
    for platform in platforms:
        result.append({
            "id": platform.id,
            "name": platform.name,
            "display_name": platform.display_name,
            "type": platform.type.value if platform.type else None,
            "is_active": platform.is_active,
            "supported_asset_types": platform.supported_asset_types,
            "supported_asset_types_type": str(type(platform.supported_asset_types)),
            "created_at": platform.created_at.isoformat() if platform.created_at else None,
            "updated_at": platform.updated_at.isoformat() if platform.updated_at else None,
        })
    
    return result