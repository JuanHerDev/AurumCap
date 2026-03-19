from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.transaction_service import (
    create_transaction,
    get_transactions,
    get_transaction,
    update_transaction,
    delete_transaction,
)
from app.schemas.transactions import TransactionRequest, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_tx(
    data: TransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_transaction(data, current_user, db)


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_transactions(current_user, db, limit, offset)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_tx(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_transaction(transaction_id, current_user, db)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_tx(
    transaction_id: int,
    data: TransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_transaction(transaction_id, data, current_user, db)


@router.delete("/{transaction_id}", status_code=204)
async def delete_tx(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_transaction(transaction_id, current_user, db)