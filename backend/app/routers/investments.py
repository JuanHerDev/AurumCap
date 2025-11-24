from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
import asyncio
import logging
import traceback
from datetime import datetime

from app.db.database import get_db
from app.schemas.investment import (
    InvestmentCreate, 
    InvestmentOut, 
    InvestmentUpdate,
    InvestmentCreateResponse,  
    AggregatedHolding,         
    AggregatedHoldingsResponse 
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
    """Enhanced portfolio calculation with aggregation features"""
    
    @staticmethod
    def calculate_holding_period(inv: Investment) -> int:
        """
        Calculate days the investment has been held
        Uses created_at as acquisition date
        """
        from datetime import datetime
        if not inv.created_at:
            return 1
        
        current_time = datetime.utcnow()
        acquisition_date = inv.created_at
        
        # If the datetime has timezone info, convert to naive UTC
        if acquisition_date.tzinfo is not None:
            acquisition_date = acquisition_date.replace(tzinfo=None)
        
        days_held = (current_time - acquisition_date).days
        return max(days_held, 1)  # At least 1 day held

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
            
            # Calculate metrics
            gain_loss = current_value - invested_amount
            roi = (gain_loss / invested_amount * Decimal("100")) if invested_amount > 0 else Decimal("0")
            
            # Calculate holding period
            holding_days = PortfolioCalculator.calculate_holding_period(inv)
            
            # Calculate annualized ROI
            annualized_roi = Decimal("0")
            if holding_days > 1 and gain_loss > 0:
                annualized_roi = ((1 + (gain_loss / invested_amount)) ** (Decimal("365") / Decimal(str(holding_days))) - 1) * Decimal("100")
            
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
                "holding_days": holding_days,
                "annualized_roi": annualized_roi,
                "acquisition_date": inv.created_at.date().isoformat() if inv.created_at else None,
                "currency": inv.currency,
                "fundamentals": fundamentals,
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
                "holding_days": 1,
                "annualized_roi": Decimal("0"),
                "acquisition_date": None,
                "currency": inv.currency,
                "fundamentals": {},
                "error": str(e)
            }

    @staticmethod
    def _round_decimal(value: Decimal) -> Decimal:
        """Round decimal to 2 decimal places for display"""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    
    @staticmethod
    def calculate_aggregated_holdings(investments: List[Investment]) -> Dict[str, Any]:
        """
        Calculate aggregated holdings for the same assets across multiple purchases
        """
        aggregated = {}
        
        for inv in investments:
            symbol = inv.symbol
            quantity = Decimal(str(inv.quantity))
            invested_amount = Decimal(str(inv.invested_amount))
            
            if symbol not in aggregated:
                aggregated[symbol] = {
                    "symbol": symbol,
                    "asset_name": inv.asset_name,
                    "asset_type": inv.asset_type,
                    "total_quantity": Decimal("0"),
                    "total_invested": Decimal("0"),
                    "purchases": [],
                    "purchase_count": 0,
                    "currency": inv.currency
                }
            
            aggregated[symbol]["total_quantity"] += quantity
            aggregated[symbol]["total_invested"] += invested_amount
            aggregated[symbol]["purchase_count"] += 1
            aggregated[symbol]["purchases"].append({
                "id": inv.id,
                "quantity": quantity,
                "invested_amount": invested_amount,
                "purchase_price": Decimal(str(inv.purchase_price)),
                "acquisition_date": inv.created_at,
                "individual_roi": None
            })
        
        # Calculate average purchase price for each symbol
        for symbol, data in aggregated.items():
            if data["total_quantity"] > 0:
                data["average_price"] = data["total_invested"] / data["total_quantity"]
            else:
                data["average_price"] = Decimal("0")
        
        return aggregated

    @staticmethod
    async def calculate_aggregated_holdings_with_prices(investments: List[Investment]) -> Dict[str, Any]:
        """
        Calculate aggregated holdings with current prices and ROI
        """
        aggregated = PortfolioCalculator.calculate_aggregated_holdings(investments)
        
        # Get current prices for all unique symbols
        unique_symbols = list(aggregated.keys())
        price_tasks = []
        
        for symbol in unique_symbols:
            # Get any investment with this symbol for asset info
            sample_inv = next((inv for inv in investments if inv.symbol == symbol), None)
            if sample_inv:
                price_tasks.append(PortfolioCalculator._get_asset_price(sample_inv))
            else:
                price_tasks.append(asyncio.sleep(0))  # Placeholder
        
        current_prices = await asyncio.gather(*price_tasks)
        
        # Update aggregated data with prices and ROI
        aggregated_with_prices = {}
        for i, symbol in enumerate(unique_symbols):
            data = aggregated[symbol]
            current_price = current_prices[i] if i < len(current_prices) else Decimal("0")
            current_value = data["total_quantity"] * current_price
            total_invested = data["total_invested"]
            gain_loss = current_value - total_invested
            roi_percentage = (gain_loss / total_invested * Decimal("100")) if total_invested > 0 else Decimal("0")
            
            aggregated_with_prices[symbol] = {
                **data,
                "current_price": current_price,
                "current_value": current_value,
                "gain_loss": gain_loss,
                "roi_percentage": roi_percentage
            }
        
        return aggregated_with_prices

    @staticmethod
    def get_user_asset_context(db: Session, user_id: int, symbol: str) -> Dict[str, Any]:
        """
        Get context about user's existing holdings for a symbol
        """
        investments = list_investments(db, user_id)
        user_symbols = [inv.symbol for inv in investments]
        
        existing_holdings = [inv for inv in investments if inv.symbol == symbol]
        existing_count = len(existing_holdings)
        
        if existing_count > 0:
            total_invested = sum(Decimal(str(inv.invested_amount)) for inv in existing_holdings)
            total_quantity = sum(Decimal(str(inv.quantity)) for inv in existing_holdings)
            average_price = total_invested / total_quantity if total_quantity > 0 else Decimal("0")
        else:
            total_invested = Decimal("0")
            total_quantity = Decimal("0")
            average_price = Decimal("0")
        
        return {
            "has_existing_holdings": existing_count > 0,
            "existing_holdings_count": existing_count,
            "total_invested_in_asset": total_invested,
            "total_quantity": total_quantity,
            "average_price": average_price,
            "user_assets": user_symbols
        }

    @staticmethod
    async def calculate_portfolio_summary(investments: List[Investment]) -> Dict[str, Any]:
        """
        Calculate portfolio summary with concurrent processing AND aggregation
        """
        if not investments:
            return {
                "total_invested": Decimal("0"),
                "current_value": Decimal("0"),
                "total_gain_loss": Decimal("0"),
                "total_roi_percentage": Decimal("0"),
                "items": [],
                "aggregated_holdings": {},
                "asset_allocation": {},
                "performance_metrics": {}
            }

        # Process all investments concurrently
        tasks = [PortfolioCalculator._process_investment(inv) for inv in investments]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate aggregated holdings (NUEVO)
        aggregated_holdings = await PortfolioCalculator.calculate_aggregated_holdings_with_prices(investments)
        
        # Process results (código existente)
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
            "aggregated_holdings": aggregated_holdings,  # NUEVO
            "asset_allocation": asset_allocation,
            "performance_metrics": performance_metrics
        }



@router.post(
    "",
    response_model=InvestmentCreateResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Investment",
    description="Create a new investment - Same button for new purchases and adding to existing holdings"
)
def create_inv(
    payload: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new investment - USER-FRIENDLY VERSION
    - Same button for new assets and adding to existing ones
    - Returns context about the holding
    """
    try:
        logger.info(f"🔄 Creating investment for user {current_user.id} - Asset: {payload.symbol}")
        
        # Check user's existing holdings for this symbol (CONTEXTO USER-FRIENDLY)
        holding_context = PortfolioCalculator.get_user_asset_context(db, current_user.id, payload.symbol)
        
        # Create the investment
        result = create_investment(db, current_user.id, payload)
        
        # Prepare user-friendly response
        if holding_context["has_existing_holdings"]:
            message = f"Added to your existing {payload.symbol} holding"
            context_type = "added_to_existing"
        else:
            message = f"New {payload.symbol} holding created"
            context_type = "new_holding"
        
        # Crear respuesta user-friendly
        response_data = InvestmentCreateResponse(
            **result.__dict__,
            holding_context=context_type,
            existing_holdings_count=holding_context["existing_holdings_count"],
            total_invested_in_asset=holding_context["total_invested_in_asset"] + Decimal(str(payload.invested_amount)),
            average_price=holding_context["average_price"],
            message=message
        )
        
        logger.info(f"{message} - Total holdings: {holding_context['existing_holdings_count'] + 1}")
        return response_data
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvestmentCRUDError as e:
        logger.error(f"CRUD error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create investment"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Get Portfolio Summary",
    description="Get comprehensive portfolio summary with aggregated holdings"
)
async def investments_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    asset_type: Optional[str] = Query(None, description="Filter by asset type")
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


@router.get(
    "/aggregated",
    response_model=AggregatedHoldingsResponse,
    summary="Get Aggregated Holdings",
    description="Get portfolio holdings aggregated by symbol with average prices and consolidated ROI"
)
async def aggregated_holdings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregated holdings with average purchase prices and consolidated ROI
    """
    try:
        logger.info(f"Calculating aggregated holdings for user {current_user.id}")
        
        investments = list_investments(db, current_user.id)
        
        # Calculate aggregated holdings with prices
        aggregated_holdings = await PortfolioCalculator.calculate_aggregated_holdings_with_prices(investments)
        
        response = AggregatedHoldingsResponse(
            aggregated_holdings=aggregated_holdings,
            total_symbols=len(aggregated_holdings),
            calculation_date=datetime.utcnow()
        )
        
        logger.info(f"Aggregated holdings calculated for user {current_user.id}: {len(aggregated_holdings)} symbols")
        return response
        
    except Exception as e:
        logger.error(f"Error calculating aggregated holdings for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculating aggregated holdings"
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
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
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
    Test endpoint for creating a simple investment
    """
    try:
        print("[TEST SIMPLE] Starting test...")
        
        from decimal import Decimal
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
        )
        
        db.add(investment)
        db.commit()
        db.refresh(investment)
        
        print(f"[TEST SIMPLE] Test investment created: {investment.id}")
        return investment
        
    except Exception as e:
        print(f"[TEST SIMPLE] Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
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
    TEST using raw SQL to create an investment
    """
    try:
        print("🔍 [RAW SQL] Starting raw SQL test")
        
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
        
        print(f"[RAW SQL SUCCESS] Investment {investment_id} created via raw SQL")
        

        investment = db.query(Investment).filter(Investment.id == investment_id).first()
        return investment
        
    except Exception as e:
        db.rollback()
        print(f"[RAW SQL ERROR] {str(e)}")
        import traceback
        print(f"[RAW SQL TRACEBACK] {traceback.format_exc()}")
        raise HTTPException(500, f"Raw SQL test failed: {str(e)}")
    

@router.post("/test-identify-field")
def test_identify_field(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    TEST for identifying date fields and their behavior
    """
    try:
        print("[FIELD ID] Starting field identification test")
        

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
        
        print(f"[FIELD ID] Investment {investment_id} created")
        

        investment = db.query(Investment).filter(Investment.id == investment_id).first()
        

        print("🔍 [FIELD ID] Testing date fields:")
        

        try:
            print(f"Testing created_at: {investment.created_at}")
            print(f"created_at type: {type(investment.created_at)}")
            print(f"created_at tzinfo: {investment.created_at.tzinfo}")
            _ = investment.created_at.isoformat()
            print("created_at OK")
        except Exception as e:
            print(f" created_at ERROR: {e}")
        

        try:
            print(f"Testing updated_at: {investment.updated_at}")
            print(f"updated_at type: {type(investment.updated_at)}")
            print(f"updated_at tzinfo: {investment.updated_at.tzinfo}")
            _ = investment.updated_at.isoformat()
            print("updated_at OK")
        except Exception as e:
            print(f"updated_at ERROR: {e}")
        
        print("[FIELD ID] All fields tested individually")
        return investment
        
    except Exception as e:
        print(f"[FIELD ID ERROR] {str(e)}")
        import traceback
        print(f"[FIELD ID TRACEBACK] {traceback.format_exc()}")
        raise HTTPException(500, f"Field ID test failed: {str(e)}")

@router.post("/test-manual-response")
def test_manual_response(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    TEST for manually constructing and returning a response
    """
    try:
        print("🔍 [MANUAL RESPONSE] Starting manual response test")
        

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
        
        print(f"[MANUAL RESPONSE] Investment {investment_id} created")
        

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
            "created_at": None,
            "updated_at": None,
            "platform_id": None,
            "coingecko_id": None,
            "twelvedata_id": None
        }
        
        print("[MANUAL RESPONSE] Returning manual response")
        return manual_response
        
    except Exception as e:
        print(f"[MANUAL RESPONSE ERROR] {str(e)}")
        raise HTTPException(500, f"Manual response test failed: {str(e)}")