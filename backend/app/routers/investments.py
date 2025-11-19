from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal, ROUND_HALF_UP
from app.db.database import get_db
from app.schemas.investment import InvestmentCreate, InvestmentOut, InvestmentUpdate
from app.crud.investment import (
    create_investment, get_investment, list_investments,
    update_investment, delete_investment
)
from app.utils.users.user import get_current_user
from app.models.user import User

# Services API (sync)
from app.services.prices_crypto import get_crypto_price
from app.services.prices_stocks import get_stock_price
from app.services.fundamentals import get_fundamentals

router = APIRouter(
    prefix="/investments",
    tags=["Investments"]
)


# --------------------------------------------------------
# SUMMARY
# --------------------------------------------------------
@router.get("/summary")
async def investments_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    investments = list_investments(db, current_user.id)

    total_invested = Decimal("0")
    current_value = Decimal("0")
    items = []

    for inv in investments:

        # --- Convertir correctamente ---
        quantity = Decimal(str(inv.quantity or "0"))
        invested = Decimal(str(inv.invested_amount or "0"))

        # --- PRICE ---
        if inv.asset_type == "crypto":
            price_float = get_crypto_price(inv.symbol)
        else:
            price_float = get_stock_price(inv.symbol)

        price = Decimal(str(price_float or 0))
        value = quantity * price

        # --- FUNDAMENTALS ---
        fundamentals = {}
        if inv.asset_type == "stock":
            fundamentals = get_fundamentals(inv.symbol)

        # --- Acumulados ---
        total_invested += invested
        current_value += value

        items.append({
            "symbol": inv.symbol,
            "asset_name": inv.asset_name,
            "asset_type": inv.asset_type,
            "quantity": quantity,
            "current_price": price,
            "current_value": value,
            "fundamentals": fundamentals
        })

    gain_loss = current_value - total_invested
    roi = (gain_loss / total_invested * Decimal("100")) if total_invested > 0 else Decimal("0")

    def r(x: Decimal):
        return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "total_invested": r(total_invested),
        "current_value": r(current_value),
        "gain_loss": r(gain_loss),
        "roi": r(roi),
        "items": items
    }



# --------------------------------------------------------
# CRUD
# --------------------------------------------------------

@router.post("", response_model=InvestmentOut)
def create_inv(
    payload: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_investment(db, current_user.id, payload)


@router.get("", response_model=List[InvestmentOut])
def read_investments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return list_investments(db, current_user.id, skip, limit)


@router.get("/{inv_id}", response_model=InvestmentOut)
def read_investment(
    inv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = get_investment(db, inv_id, current_user.id)
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")
    return inv


@router.patch("/{inv_id}", response_model=InvestmentOut)
def patch_investment(
    inv_id: int,
    payload: InvestmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = get_investment(db, inv_id, current_user.id)
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")

    return update_investment(db, inv, payload.model_dump(exclude_unset=True))


@router.delete("/{inv_id}", status_code=204)
def remove_investment(
    inv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = get_investment(db, inv_id, current_user.id)
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")

    delete_investment(db, inv, current_user.id)
    return
