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
from app.models.platform import Platform

# External services
from app.services.prices_crypto import get_crypto_price
from app.services.prices_stocks import get_stock_price
from app.services.fundamentals import get_fundamentals

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/investments",
    tags=["investments"]
)

# Investment strategies
INVESTMENT_STRATEGIES = [
    {"value": "dca", "label": "DCA (Promedio de Costo en Dólares)"},
    {"value": "lump_sum", "label": "Inversión Única"},
    {"value": "swing_trading", "label": "Swing Trading"},
    {"value": "day_trading", "label": "Day Trading"},
    {"value": "long_term", "label": "Inversión a Largo Plazo"},
    {"value": "arbitrage", "label": "Arbitraje"},
    {"value": "other", "label": "Otra Estrategia"},
]

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
        Get current price for an investment asset - FIXED VERSION
        """
        try:
            if inv.asset_type == "crypto":
                price = await get_crypto_price(inv.symbol)
            elif inv.asset_type == "stock":
                # Asegurarse de que get_stock_price retorna Decimal, no await
                price = get_stock_price(inv.symbol)  # Sin await si es síncrono
            else:
                price = Decimal("0")
            
            # Asegurar que el precio es Decimal
            if price and not isinstance(price, Decimal):
                return Decimal(str(price))
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
    description="Create a new investment - Automatically stacks with existing holdings"
)
def create_inv(
    payload: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new investment - AUTO-STACKING VERSION with DEBUG
    """
    try:
        logger.info(f"🔄 [DEBUG] Creating/updating investment for user {current_user.id}")
        logger.info(f"📦 [DEBUG] Payload received: symbol={payload.symbol}, platform_id={payload.platform_id}, strategy={payload.investment_strategy}")
        
        # Si no se proporciona transaction_date, usar la fecha actual
        if not payload.transaction_date:
            payload.transaction_date = datetime.utcnow()
            logger.info(f"📅 [DEBUG] Using current date as transaction date: {payload.transaction_date}")
        else:
            logger.info(f"📅 [DEBUG] Using provided transaction date: {payload.transaction_date}")
        
        # DEBUG: Ver todas las inversiones existentes del usuario
        all_user_investments = db.query(Investment).filter(
            Investment.user_id == current_user.id
        ).all()
        
        logger.info(f"📊 [DEBUG] User has {len(all_user_investments)} total investments:")
        for inv in all_user_investments:
            logger.info(f"   📍 ID:{inv.id} - {inv.symbol} (platform: {inv.platform_id}, strategy: {inv.investment_strategy}), Qty: {inv.quantity}")
        
        # Buscar inversión existente con el mismo símbolo y criterios
        logger.info(f"🔍 [DEBUG] Searching for existing investment: symbol={payload.symbol.upper()}, platform_id={payload.platform_id}, strategy={payload.investment_strategy}")
        
        # Construir query de búsqueda con criterios mejorados
        query = db.query(Investment).filter(
            Investment.user_id == current_user.id,
            Investment.symbol == payload.symbol.upper()
        )
        
        # Si platform_id está presente, filtrar por él
        if payload.platform_id is not None:
            query = query.filter(Investment.platform_id == payload.platform_id)
            logger.info(f"🔍 [DEBUG] Using platform filter: {payload.platform_id}")
        else:
            logger.info("🔍 [DEBUG] No platform filter - searching any platform")
            query = query.filter(Investment.platform_id.is_(None))
        
        # Si investment_strategy está presente, filtrar por ella también
        if payload.investment_strategy:
            query = query.filter(Investment.investment_strategy == payload.investment_strategy)
            logger.info(f"🔍 [DEBUG] Using strategy filter: {payload.investment_strategy}")
        else:
            logger.info("🔍 [DEBUG] No strategy filter - searching any strategy")
        
        existing_investment = query.first()
        
        logger.info(f"🔍 [DEBUG] Search result: {existing_investment}")
        
        if existing_investment:
            # ACTUALIZAR inversión existente (STACKING)
            logger.info(f"📦 [DEBUG] STACKING with existing investment {existing_investment.id}")
            logger.info(f"📦 [DEBUG] Existing: Qty={existing_investment.quantity}, Invested={existing_investment.invested_amount}, Strategy={existing_investment.investment_strategy}")
            logger.info(f"📦 [DEBUG] New: Qty={payload.quantity}, Invested={payload.invested_amount}, Strategy={payload.investment_strategy}")
            
            try:
                # Calcular nuevos valores con manejo seguro de Decimal
                existing_quantity = Decimal(str(existing_investment.quantity))
                existing_invested = Decimal(str(existing_investment.invested_amount))
                new_quantity = existing_quantity + Decimal(str(payload.quantity))
                new_invested_amount = existing_invested + Decimal(str(payload.invested_amount))
                
                logger.info(f"🧮 [DEBUG] Calculations:")
                logger.info(f"   Existing Qty: {existing_quantity}")
                logger.info(f"   New Qty: {Decimal(str(payload.quantity))}")
                logger.info(f"   Total Qty: {new_quantity}")
                logger.info(f"   Existing Invested: {existing_invested}")
                logger.info(f"   New Invested: {Decimal(str(payload.invested_amount))}")
                logger.info(f"   Total Invested: {new_invested_amount}")
                
                # Calcular nuevo precio promedio
                new_purchase_price = new_invested_amount / new_quantity if new_quantity > 0 else Decimal("0")
                logger.info(f"   New Avg Price: {new_purchase_price}")
                
                # Actualizar inversión existente
                existing_investment.quantity = new_quantity
                existing_investment.invested_amount = new_invested_amount
                existing_investment.purchase_price = new_purchase_price
                existing_investment.updated_at = datetime.utcnow()
                
                # Actualizar campos adicionales si están presentes en el payload
                if payload.investment_strategy and not existing_investment.investment_strategy:
                    existing_investment.investment_strategy = payload.investment_strategy
                    logger.info(f"📝 [DEBUG] Updated strategy to: {payload.investment_strategy}")
                
                if payload.transaction_date:
                    existing_investment.transaction_date = payload.transaction_date
                    logger.info(f"📝 [DEBUG] Updated transaction date to: {payload.transaction_date}")
                
                if payload.asset_name and not existing_investment.asset_name:
                    existing_investment.asset_name = payload.asset_name
                    logger.info(f"📝 [DEBUG] Updated asset name to: {payload.asset_name}")
                
                db.commit()
                db.refresh(existing_investment)
                
                logger.info(f"✅ [DEBUG] Investment updated successfully: ID={existing_investment.id}")
                
                # Preparar respuesta
                message = f"Added to your existing {payload.symbol} holding"
                context_type = "added_to_existing"
                result = existing_investment
                
            except Exception as calc_error:
                logger.error(f"❌ [DEBUG] Error in stacking calculation: {calc_error}")
                db.rollback()
                raise InvestmentCRUDError(f"Error stacking investments: {str(calc_error)}")
            
        else:
            # CREAR nueva inversión
            logger.info(f"🆕 [DEBUG] No existing investment found - CREATING NEW")
            
            # Asegurar que purchase_price esté calculado si no se proporciona
            if not payload.purchase_price and payload.quantity and payload.invested_amount:
                calculated_price = Decimal(str(payload.invested_amount)) / Decimal(str(payload.quantity))
                payload.purchase_price = calculated_price.quantize(Decimal('0.000001'))
                logger.info(f"🧮 [DEBUG] Auto-calculated purchase price: {payload.purchase_price}")
            
            result = create_investment(db, current_user.id, payload)
            message = f"New {payload.symbol} holding created"
            context_type = "new_holding"
            logger.info(f"✅ [DEBUG] New investment created: ID={result.id}")
        
        # Obtener contexto actualizado de todas las holdings de este símbolo
        all_symbol_holdings = db.query(Investment).filter(
            Investment.user_id == current_user.id,
            Investment.symbol == payload.symbol.upper()
        ).all()
        
        logger.info(f"📊 [DEBUG] All holdings for {payload.symbol}: {len(all_symbol_holdings)} entries")
        
        # Calcular métricas agregadas
        total_invested_in_asset = Decimal("0")
        total_quantity = Decimal("0")
        
        for inv in all_symbol_holdings:
            total_invested_in_asset += Decimal(str(inv.invested_amount))
            total_quantity += Decimal(str(inv.quantity))
            logger.info(f"   💰 Holding {inv.id}: Qty={inv.quantity}, Invested={inv.invested_amount}, Strategy={inv.investment_strategy}")
        
        average_price = total_invested_in_asset / total_quantity if total_quantity > 0 else Decimal("0")
        
        logger.info(f"📈 [DEBUG] Aggregate metrics: Total Qty={total_quantity}, Total Invested={total_invested_in_asset}, Avg Price={average_price}")
        
        # Crear respuesta user-friendly usando to_dict() para incluir todos los campos
        investment_dict = result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
        
        response_data = InvestmentCreateResponse(
            **investment_dict,
            holding_context=context_type,
            existing_holdings_count=len(all_symbol_holdings),
            total_invested_in_asset=total_invested_in_asset,
            average_price=average_price,
            message=message
        )
        
        logger.info(f"✅ {message} - Total holdings: {len(all_symbol_holdings)}, Total invested: {total_invested_in_asset}")
        return response_data
        
    except ValidationError as e:
        logger.warning(f"❌ [DEBUG] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvestmentCRUDError as e:
        logger.error(f"❌ [DEBUG] CRUD error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create investment"
        )
    except Exception as e:
        logger.error(f"❌ [DEBUG] Unexpected error: {str(e)}")
        import traceback
        logger.error(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
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
        
        # Prepare data for update - exclude unset and None values
        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

        logger.info(f"[UPDATE] Updating investment {inv_id} for user {current_user.id} with data: {update_data}")

        return update_investment(db, inv, update_data)
        
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

# NUEVOS ENDPOINTS PARA PLATAFORMAS Y ESTRATEGIAS

@router.get("/platforms/list", response_model=List[Dict[str, Any]])
async def get_platforms_list(
    asset_type: Optional[str] = Query(None, description="Filter by supported asset type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available investment platforms
    """
    try:
        from app.crud.investment import get_platforms_by_asset_type, get_active_platforms
        
        if asset_type:
            # Mapear asset_type del frontend al backend
            asset_type_mapping = {
                "stocks": "stock",
                "crypto": "crypto", 
                "etf": "etf",
                "bond": "bond",
                "real_estate": "real_estate",
                "commodity": "commodity",
                "cash": "cash",
                "otros": "other"
            }
            backend_asset_type = asset_type_mapping.get(asset_type, asset_type)
            platforms = get_platforms_by_asset_type(db, backend_asset_type)
        else:
            platforms = get_active_platforms(db)
        
        # Format response for frontend
        platform_list = []
        for platform in platforms:
            platform_list.append({
                "value": platform.name,  # Usar name como value para el frontend
                "label": platform.display_name,
                "category": platform.type.value if platform.type else platform.type,
                "icon": platform.icon,
                "supported_asset_types": platform.supported_asset_types
            })
        
        # Si no hay plataformas en la base de datos, devolver las predefinidas
        if not platform_list:
            platform_list = [
                {"value": "binance", "label": "Binance", "category": "exchange", "icon": "binance", "supported_asset_types": ["crypto"]},
                {"value": "hapi", "label": "Hapi", "category": "exchange", "icon": "hapi", "supported_asset_types": ["crypto"]},
                {"value": "etoro", "label": "eToro", "category": "broker", "icon": "etoro", "supported_asset_types": ["stock", "crypto", "etf"]},
                {"value": "interactive_brokers", "label": "Interactive Brokers", "category": "broker", "icon": "ibkr", "supported_asset_types": ["stock", "etf", "bond"]},
                {"value": "coinbase", "label": "Coinbase", "category": "exchange", "icon": "coinbase", "supported_asset_types": ["crypto"]},
                {"value": "kraken", "label": "Kraken", "category": "exchange", "icon": "kraken", "supported_asset_types": ["crypto"]},
                {"value": "fidelity", "label": "Fidelity", "category": "broker", "icon": "fidelity", "supported_asset_types": ["stock", "etf", "bond"]},
                {"value": "vanguard", "label": "Vanguard", "category": "broker", "icon": "vanguard", "supported_asset_types": ["stock", "etf", "bond"]},
                {"value": "metatrader", "label": "MetaTrader", "category": "broker", "icon": "metatrader", "supported_asset_types": ["forex", "crypto"]},
                {"value": "other", "label": "Otra Plataforma", "category": "other", "icon": "other", "supported_asset_types": ["stock", "crypto", "etf", "bond", "real_estate", "commodity", "other"]}
            ]
            
            # Filtrar por asset_type si se especificó
            if asset_type:
                backend_asset_type = asset_type_mapping.get(asset_type, asset_type)
                platform_list = [p for p in platform_list if backend_asset_type in p["supported_asset_types"]]
        
        return platform_list
        
    except Exception as e:
        logger.error(f"Error retrieving platforms: {e}")
        # Fallback to predefined platforms
        return [
            {"value": "binance", "label": "Binance", "category": "exchange"},
            {"value": "hapi", "label": "Hapi", "category": "exchange"},
            {"value": "etoro", "label": "eToro", "category": "broker"},
            {"value": "interactive_brokers", "label": "Interactive Brokers", "category": "broker"},
            {"value": "coinbase", "label": "Coinbase", "category": "exchange"},
            {"value": "kraken", "label": "Kraken", "category": "exchange"},
            {"value": "fidelity", "label": "Fidelity", "category": "broker"},
            {"value": "vanguard", "label": "Vanguard", "category": "broker"},
            {"value": "metatrader", "label": "MetaTrader", "category": "broker"},
            {"value": "other", "label": "Otra Plataforma", "category": "other"}
        ]

@router.get("/strategies/list", response_model=List[Dict[str, str]])
async def get_strategies_list():
    """
    Get all available investment strategies
    """
    return INVESTMENT_STRATEGIES


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
    
@router.get("/debug/user-holdings")
def debug_user_holdings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to see all user holdings"""
    investments = db.query(Investment).filter(
        Investment.user_id == current_user.id
    ).order_by(Investment.symbol, Investment.created_at).all()
    
    result = []
    for inv in investments:
        result.append({
            "id": inv.id,
            "symbol": inv.symbol,
            "platform_id": inv.platform_id,
            "quantity": str(inv.quantity),
            "invested_amount": str(inv.invested_amount),
            "purchase_price": str(inv.purchase_price),
            "asset_type": inv.asset_type,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
        })
    
    # Agrupar por símbolo para ver stacking potencial
    symbols = {}
    for inv in investments:
        symbol = inv.symbol
        if symbol not in symbols:
            symbols[symbol] = []
        symbols[symbol].append({
            "id": inv.id,
            "platform_id": inv.platform_id,
            "quantity": str(inv.quantity)
        })
    
    return {
        "user_id": current_user.id,
        "total_investments": len(investments),
        "investments": result,
        "grouped_by_symbol": symbols
    }