from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
import asyncio
import logging
import traceback

from app.db.database import get_db
from app.schemas.investment import (
    InvestmentCreate, 
    InvestmentOut, 
    InvestmentUpdate
)
from app.crud.investment import (
    create_investment, 
    get_investment, 
    list_investments,
    update_investment, 
    delete_investment,
    InvestmentCRUDError,
    ValidationError
)
from app.deps.auth import get_current_user
from app.models.user import User
from app.models.investment import Investment

# External services
from app.services.prices_crypto import get_crypto_price
from app.services.prices_stocks import get_stock_price
from app.services.fundamentals import get_fundamentals

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/investments",
    tags=["investments"]
)


class PortfolioCalculator:
    """Enhanced portfolio calculation with concurrent processing"""
    
    @staticmethod
    async def _get_asset_price(inv: Investment) -> Decimal:
        """
        Get current price for an investment asset
        """
        try:
            if inv.asset_type == "crypto":
                price = await get_crypto_price(inv.symbol)
            elif inv.asset_type == "stock":
                price = await get_stock_price(inv.symbol)
            else:
                price = Decimal("0")
                
            return price or Decimal("0")
        except Exception as e:
            logger.error(f"Error fetching price for {inv.symbol}: {e}")
            return Decimal("0")

    @staticmethod
    async def _process_investment(inv: Investment) -> Dict[str, Any]:
        """
        Process a single investment and return its current state
        """
        try:
            quantity = Decimal(str(inv.quantity))
            invested_amount = Decimal(str(inv.invested_amount))
            
            # Get current price concurrently
            current_price = await PortfolioCalculator._get_asset_price(inv)
            current_value = quantity * current_price
            
            # Get fundamentals for stocks
            fundamentals = {}
            if inv.asset_type == "stock":
                try:
                    fundamentals = get_fundamentals(inv.symbol) or {}
                except Exception as e:
                    logger.warning(f"Could not get fundamentals for {inv.symbol}: {e}")
            
            gain_loss = current_value - invested_amount
            roi = (gain_loss / invested_amount * Decimal("100")) if invested_amount > 0 else Decimal("0")
            
            return {
                "id": inv.id,
                "symbol": inv.symbol,
                "asset_name": inv.asset_name,
                "asset_type": inv.asset_type,
                "quantity": quantity,
                "invested_amount": invested_amount,
                "purchase_price": Decimal(str(inv.purchase_price)),
                "current_price": current_price,
                "current_value": current_value,
                "gain_loss": gain_loss,
                "roi_percentage": roi,
                "currency": inv.currency,
                "fundamentals": fundamentals,
                "date_acquired": inv.date_acquired,
                "platform_id": inv.platform_id,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error processing investment {inv.id}: {e}")
            return {
                "id": inv.id,
                "symbol": inv.symbol,
                "asset_name": inv.asset_name,
                "asset_type": inv.asset_type,
                "quantity": Decimal(str(inv.quantity)),
                "invested_amount": Decimal(str(inv.invested_amount)),
                "current_price": Decimal("0"),
                "current_value": Decimal("0"),
                "gain_loss": -Decimal(str(inv.invested_amount)),
                "roi_percentage": Decimal("-100"),
                "currency": inv.currency,
                "fundamentals": {},
                "error": str(e)
            }

    @staticmethod
    def _round_decimal(value: Decimal) -> Decimal:
        """Round decimal to 2 decimal places for display"""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    async def calculate_portfolio_summary(investments: List[Investment]) -> Dict[str, Any]:
        """
        Calculate portfolio summary with concurrent processing
        """
        if not investments:
            return {
                "total_invested": Decimal("0"),
                "current_value": Decimal("0"),
                "total_gain_loss": Decimal("0"),
                "total_roi_percentage": Decimal("0"),
                "items": [],
                "asset_allocation": {},
                "performance_metrics": {}
            }

        # Process all investments concurrently
        tasks = [PortfolioCalculator._process_investment(inv) for inv in investments]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_items = []
        total_invested = Decimal("0")
        total_current_value = Decimal("0")
        asset_allocation = {}
        
        for i, result in enumerate(results):
            investment = investments[i]
            
            if isinstance(result, Exception):
                logger.error(f"Error processing investment {investment.id}: {result}")
                continue
                
            valid_items.append(result)
            total_invested += result["invested_amount"]
            total_current_value += result["current_value"]
            
            # Calculate asset allocation
            asset_type = result["asset_type"]
            allocation_percentage = (result["invested_amount"] / total_invested * Decimal("100")) if total_invested > 0 else Decimal("0")
            
            if asset_type not in asset_allocation:
                asset_allocation[asset_type] = {
                    "total_invested": Decimal("0"),
                    "total_value": Decimal("0"),
                    "allocation_percentage": Decimal("0"),
                    "count": 0
                }
                
            asset_allocation[asset_type]["total_invested"] += result["invested_amount"]
            asset_allocation[asset_type]["total_value"] += result["current_value"]
            asset_allocation[asset_type]["count"] += 1
        
        # Calculate allocation percentages
        for asset_type in asset_allocation:
            allocation = asset_allocation[asset_type]
            allocation["allocation_percentage"] = (allocation["total_invested"] / total_invested * Decimal("100")) if total_invested > 0 else Decimal("0")
        
        # Calculate overall metrics
        total_gain_loss = total_current_value - total_invested
        total_roi_percentage = (total_gain_loss / total_invested * Decimal("100")) if total_invested > 0 else Decimal("0")
        
        # Performance metrics
        best_performer = max(valid_items, key=lambda x: x["roi_percentage"]) if valid_items else None
        worst_performer = min(valid_items, key=lambda x: x["roi_percentage"]) if valid_items else None
        
        performance_metrics = {
            "best_performer": best_performer["symbol"] if best_performer else None,
            "best_roi": PortfolioCalculator._round_decimal(best_performer["roi_percentage"]) if best_performer else Decimal("0"),
            "worst_performer": worst_performer["symbol"] if worst_performer else None,
            "worst_roi": PortfolioCalculator._round_decimal(worst_performer["roi_percentage"]) if worst_performer else Decimal("0"),
            "total_assets": len(valid_items),
            "profitable_assets": len([item for item in valid_items if item["gain_loss"] > 0]),
            "losing_assets": len([item for item in valid_items if item["gain_loss"] < 0])
        }
        
        return {
            "total_invested": PortfolioCalculator._round_decimal(total_invested),
            "current_value": PortfolioCalculator._round_decimal(total_current_value),
            "total_gain_loss": PortfolioCalculator._round_decimal(total_gain_loss),
            "total_roi_percentage": PortfolioCalculator._round_decimal(total_roi_percentage),
            "items": valid_items,
            "asset_allocation": asset_allocation,
            "performance_metrics": performance_metrics
        }


@router.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Get Portfolio Summary",
    description="Get comprehensive portfolio summary with current values, performance metrics, and asset allocation"
)
async def investments_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    asset_type: Optional[str] = Query(None, description="Filter by asset type")  # ✅ CAMBIADO: AssetType -> str
):
    """
    Get comprehensive portfolio summary with concurrent price fetching
    """
    try:
        logger.info(f"Generating portfolio summary for user {current_user.id}")
        
        # Get investments with optional filtering
        investments = list_investments(db, current_user.id, asset_type=asset_type)
        
        # Calculate portfolio summary
        summary = await PortfolioCalculator.calculate_portfolio_summary(investments)
        
        logger.info(f"Portfolio summary generated for user {current_user.id}: {len(investments)} investments")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating portfolio summary for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating portfolio summary"
        )

@router.post(
    "",
    response_model=InvestmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Investment",
    description="Create a new investment with automatic purchase price calculation"
)
def create_inv(
    payload: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new investment - CON DEBUG MEJORADO
    """
    try:
        logger.info(f"🔄 Creating investment for user {current_user.id}")
        logger.info(f"📦 Investment data: {payload.model_dump()}")
        
        # ✅ DEBUG DETALLADO: Verificar date_acquired
        if payload.date_acquired:
            logger.info(f"📅 date_acquired: {payload.date_acquired}")
            logger.info(f"📅 date_acquired type: {type(payload.date_acquired)}")
            logger.info(f"📅 date_acquired tzinfo: {payload.date_acquired.tzinfo}")
        else:
            logger.info("📅 date_acquired: None (will use current time)")
        
        result = create_investment(db, current_user.id, payload)
        logger.info(f"✅ Investment created successfully: {result.id}")
        return result
        
    except ValidationError as e:
        logger.warning(f"❌ Validation error creating investment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvestmentCRUDError as e:
        logger.error(f"❌ CRUD error creating investment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create investment"
        )
    except Exception as e:
        # ✅ CAPTURAR EL ERROR REAL CON DETALLES
        logger.error(f"💥 UNEXPECTED ERROR in create_investment: {str(e)}")
        logger.error(f"💥 Error type: {type(e)}")
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error creating investment: {str(e)}"
        )


@router.get(
    "",
    response_model=List[InvestmentOut],
    summary="List Investments",
    description="Get paginated list of user's investments"
)
def read_investments(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),  # ✅ CAMBIADO: AssetType -> str
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user investments with pagination and filtering
    """
    try:
        return list_investments(db, current_user.id, skip, limit, asset_type)
    except Exception as e:
        logger.error(f"Error listing investments for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving investments"
        )


@router.get(
    "/{inv_id}",
    response_model=InvestmentOut,
    summary="Get Investment",
    description="Get specific investment by ID"
)
def read_investment(
    inv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific investment
    """
    inv = get_investment(db, inv_id, current_user.id)
    if not inv:
        logger.warning(f"Investment {inv_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment not found"
        )
    return inv


@router.patch(
    "/{inv_id}",
    response_model=InvestmentOut,
    summary="Update Investment",
    description="Partially update an investment"
)
def patch_investment(
    inv_id: int,
    payload: InvestmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an investment
    """
    try:
        inv = get_investment(db, inv_id, current_user.id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investment not found"
            )

        return update_investment(db, inv, payload.model_dump(exclude_unset=True))
        
    except ValidationError as e:
        logger.warning(f"Validation error updating investment {inv_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvestmentCRUDError as e:
        logger.error(f"CRUD error updating investment {inv_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update investment"
        )


@router.delete(
    "/{inv_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Investment",
    description="Delete an investment"
)
def remove_investment(
    inv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an investment
    """
    try:
        inv = get_investment(db, inv_id, current_user.id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investment not found"
            )

        delete_investment(db, inv, current_user.id)
        
    except PermissionError as e:
        logger.warning(f"Permission error deleting investment {inv_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except InvestmentCRUDError as e:
        logger.error(f"CRUD error deleting investment {inv_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete investment"
        )


@router.post(
    "/test-simple",
    response_model=InvestmentOut,
    summary="Test Create Investment (Debug)",
    description="Create a test investment with minimal data for debugging"
)
def test_create_simple(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint for creating a simple investment - CON DEBUG EXTREMO
    """
    try:
        print("🔍 [1] EXTREME DEBUG: Starting test-simple")
        
        # Crear un objeto simple que simule los datos
        class TestData:
            def __init__(self):
                self.symbol = "TEST"
                self.asset_name = "Test Asset" 
                self.asset_type = "other"
                self.invested_amount = Decimal("1000")
                self.quantity = Decimal("10")
                self.currency = "USD"
                self.platform_id = None
                self.purchase_price = None
                self.date_acquired = None
                self.coingecko_id = None
                self.twelvedata_id = None
        
        test_data = TestData()
        print("🔍 [2] TestData object created")
        
        # ✅ INTENTAR CREAR LA INVERSIÓN DIRECTAMENTE, SIN EL CRUD
        print("🔍 [3] Attempting to create Investment object directly")
        
        from datetime import datetime
        from app.models.investment import Investment
        
        # Crear la inversión directamente
        investment = Investment(
            user_id=current_user.id,
            platform_id=None,
            symbol="TEST",
            asset_name="Test Asset",
            asset_type="other", 
            invested_amount=Decimal("1000"),
            quantity=Decimal("10"),
            purchase_price=Decimal("100"),
            currency="USD",
            date_acquired=datetime.utcnow(),  # naive datetime
            # created_at y updated_at se generan automáticamente
        )
        
        print("🔍 [4] Investment object created successfully")
        print(f"🔍 [5] date_acquired: {investment.date_acquired}")
        print(f"🔍 [6] date_acquired type: {type(investment.date_acquired)}")
        print(f"🔍 [7] date_acquired tzinfo: {investment.date_acquired.tzinfo}")
        
        print("🔍 [8] Adding investment to database session")
        db.add(investment)
        
        print("🔍 [9] Committing transaction")
        db.commit()
        
        print("🔍 [10] Refreshing investment")
        db.refresh(investment)
        
        print(f"✅ [SUCCESS] Test investment created: {investment.id}")
        return investment
        
    except Exception as e:
        print(f"💥 [ERROR] Exception type: {type(e)}")
        print(f"💥 [ERROR] Exception message: {str(e)}")
        
        # ✅ CAPTURAR EL TRACEBACK COMPLETO PARA VER DÓNDE ESTÁ LA COMPARACIÓN
        import traceback
        tb = traceback.format_exc()
        print(f"💥 [TRACEBACK] Full traceback:\n{tb}")
        
        # Buscar en el traceback dónde está la comparación de fechas
        if "offset-naive and offset-aware" in str(e):
            print("🚨 [TIMEZONE ISSUE] Found the timezone comparison error!")
            # Imprimir las líneas relevantes del traceback
            for line in tb.split('\n'):
                if "datetime" in line or "compare" in line or "investment" in line.lower():
                    print(f"🔍 [RELEVANT] {line}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )
    
@router.post("/test-raw-sql")
def test_raw_sql(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    TEST usando SQL directo - evita completamente el ORM
    """
    try:
        print("🔍 [RAW SQL] Starting raw SQL test")
        
        from sqlalchemy import text
        
        # Ejecutar SQL directo
        result = db.execute(
            text("""
                INSERT INTO investments 
                (user_id, symbol, asset_name, asset_type, invested_amount, quantity, purchase_price, currency)
                VALUES 
                (:user_id, :symbol, :asset_name, :asset_type, :invested_amount, :quantity, :purchase_price, :currency)
                RETURNING id
            """),
            {
                "user_id": current_user.id,
                "symbol": "TESTRAW",
                "asset_name": "Raw SQL Test", 
                "asset_type": "other",
                "invested_amount": 100.0,
                "quantity": 10.0,
                "purchase_price": 10.0,
                "currency": "USD"
            }
        )
        
        investment_id = result.scalar()
        db.commit()
        
        print(f"✅ [RAW SQL SUCCESS] Investment {investment_id} created via raw SQL")
        
        # Recuperar la inversión creada
        investment = db.query(Investment).filter(Investment.id == investment_id).first()
        return investment
        
    except Exception as e:
        db.rollback()
        print(f"💥 [RAW SQL ERROR] {str(e)}")
        import traceback
        print(f"💥 [RAW SQL TRACEBACK] {traceback.format_exc()}")
        raise HTTPException(500, f"Raw SQL test failed: {str(e)}")
    

@router.post("/test-identify-field")
def test_identify_field(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    TEST para identificar qué campo específico causa el error de timezone
    """
    try:
        print("🔍 [FIELD ID] Starting field identification test")
        
        # Crear inversión via SQL directo (sabemos que funciona)
        from sqlalchemy import text
        result = db.execute(
            text("""
                INSERT INTO investments 
                (user_id, symbol, asset_name, asset_type, invested_amount, quantity, purchase_price, currency)
                VALUES 
                (:user_id, :symbol, :asset_name, :asset_type, :invested_amount, :quantity, :purchase_price, :currency)
                RETURNING id
            """),
            {
                "user_id": current_user.id,
                "symbol": "TESTFIELD",
                "asset_name": "Field Test", 
                "asset_type": "other",
                "invested_amount": 100.0,
                "quantity": 10.0,
                "purchase_price": 10.0,
                "currency": "USD"
            }
        )
        
        investment_id = result.scalar()
        db.commit()
        
        print(f"✅ [FIELD ID] Investment {investment_id} created")
        
        # Recuperar la inversión
        investment = db.query(Investment).filter(Investment.id == investment_id).first()
        
        # ✅ TEST INDIVIDUAL DE CADA CAMPO DE FECHA
        print("🔍 [FIELD ID] Testing individual date fields:")
        
        # Probar date_acquired
        try:
            print(f"🔍 Testing date_acquired: {investment.date_acquired}")
            print(f"🔍 date_acquired type: {type(investment.date_acquired)}")
            print(f"🔍 date_acquired tzinfo: {investment.date_acquired.tzinfo}")
            _ = investment.date_acquired.isoformat()  # Esto podría causar la comparación
            print("✅ date_acquired OK")
        except Exception as e:
            print(f"❌ date_acquired ERROR: {e}")
        
        # Probar created_at
        try:
            print(f"🔍 Testing created_at: {investment.created_at}")
            print(f"🔍 created_at type: {type(investment.created_at)}")
            print(f"🔍 created_at tzinfo: {investment.created_at.tzinfo}")
            _ = investment.created_at.isoformat()
            print("✅ created_at OK")
        except Exception as e:
            print(f"❌ created_at ERROR: {e}")
        
        # Probar updated_at
        try:
            print(f"🔍 Testing updated_at: {investment.updated_at}")
            print(f"🔍 updated_at type: {type(investment.updated_at)}")
            print(f"🔍 updated_at tzinfo: {investment.updated_at.tzinfo}")
            _ = investment.updated_at.isoformat()
            print("✅ updated_at OK")
        except Exception as e:
            print(f"❌ updated_at ERROR: {e}")
        
        print("✅ [FIELD ID] All fields tested individually")
        return investment
        
    except Exception as e:
        print(f"💥 [FIELD ID ERROR] {str(e)}")
        import traceback
        print(f"💥 [FIELD ID TRACEBACK] {traceback.format_exc()}")
        raise HTTPException(500, f"Field ID test failed: {str(e)}")

@router.post("/test-manual-response")
def test_manual_response(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    TEST que retorna una respuesta MANUAL, evitando la serialización automática
    """
    try:
        print("🔍 [MANUAL RESPONSE] Starting manual response test")
        
        # Crear inversión via SQL directo
        from sqlalchemy import text
        result = db.execute(
            text("""
                INSERT INTO investments 
                (user_id, symbol, asset_name, asset_type, invested_amount, quantity, purchase_price, currency)
                VALUES 
                (:user_id, :symbol, :asset_name, :asset_type, :invested_amount, :quantity, :purchase_price, :currency)
                RETURNING id
            """),
            {
                "user_id": current_user.id,
                "symbol": "TESTMANUAL",
                "asset_name": "Manual Test", 
                "asset_type": "other",
                "invested_amount": 100.0,
                "quantity": 10.0,
                "purchase_price": 10.0,
                "currency": "USD"
            }
        )
        
        investment_id = result.scalar()
        db.commit()
        
        print(f"✅ [MANUAL RESPONSE] Investment {investment_id} created")
        
        # ✅ RETORNAR RESPUESTA MANUAL, EVITANDO LA SERIALIZACIÓN AUTOMÁTICA
        manual_response = {
            "id": investment_id,
            "user_id": current_user.id,
            "symbol": "TESTMANUAL",
            "asset_name": "Manual Test",
            "asset_type": "other",
            "invested_amount": "100.0",
            "quantity": "10.0", 
            "purchase_price": "10.0",
            "currency": "USD",
            "date_acquired": None,  # Omitir las fechas problemáticas
            "created_at": None,
            "updated_at": None,
            "platform_id": None,
            "coingecko_id": None,
            "twelvedata_id": None
        }
        
        print("✅ [MANUAL RESPONSE] Returning manual response (no serialization)")
        return manual_response
        
    except Exception as e:
        print(f"💥 [MANUAL RESPONSE ERROR] {str(e)}")
        raise HTTPException(500, f"Manual response test failed: {str(e)}")
    
