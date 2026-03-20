from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.transaction import Transaction
from app.models.holdings import Holdings
from app.models.user import User
from app.schemas.transactions import TransactionRequest, TransactionResponse
from app.services.asset_service import get_or_create_asset
from app.services.portfolio_service import invalidate_portfolio_cache


async def create_transaction(
    data: TransactionRequest,
    user: User,
    db: AsyncSession,
) -> TransactionResponse:

    # Verify that the asset exists or create it via provider
    asset = await get_or_create_asset(str(data.asset_id), db) \
        if isinstance(data.asset_id, str) \
        else await _get_asset_by_id(data.asset_id, db)

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Create the transaction record
    transaction = Transaction(
        user_id=user.id,
        asset_id=asset.id,
        platform_id=data.platform_id,
        type=data.type,
        quantity=data.quantity,
        price=data.price,
        fees=data.fees,
        date=data.date,
        notes=data.notes,
    )
    db.add(transaction)
    await db.flush()

    # Update holdings based on BUY or SELL
    await _update_holdings(
        user_id=user.id,
        asset_id=asset.id,
        tx_type=data.type,
        quantity=data.quantity,
        price=data.price,
        db=db,
    )

    # Invalidate portfolio cache — holdings have changed
    await invalidate_portfolio_cache(user.id)

    return TransactionResponse(
        id=transaction.id,
        asset_id=asset.id,
        symbol=asset.symbol,
        type=transaction.type,
        quantity=transaction.quantity,
        price=transaction.price,
        fees=transaction.fees,
        total=round(transaction.quantity * transaction.price + transaction.fees, 4),
        date=transaction.date,
        notes=transaction.notes,
    )


async def get_transactions(
    user: User,
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[TransactionResponse]:
    from app.models.asset import Asset

    result = await db.execute(
        select(Transaction, Asset)
        .join(Asset, Transaction.asset_id == Asset.id)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.date.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()

    return [
        TransactionResponse(
            id=tx.id,
            asset_id=tx.asset_id,
            symbol=asset.symbol,
            type=tx.type,
            quantity=tx.quantity,
            price=tx.price,
            fees=tx.fees,
            total=round(tx.quantity * tx.price + tx.fees, 4),
            date=tx.date,
            notes=tx.notes,
        )
        for tx, asset in rows
    ]


async def get_transaction(
    transaction_id: int,
    user: User,
    db: AsyncSession,
) -> TransactionResponse:
    from app.models.asset import Asset

    result = await db.execute(
        select(Transaction, Asset)
        .join(Asset, Transaction.asset_id == Asset.id)
        .where(
            Transaction.id == transaction_id,
            Transaction.user_id == user.id,
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tx, asset = row
    return TransactionResponse(
        id=tx.id,
        asset_id=tx.asset_id,
        symbol=asset.symbol,
        type=tx.type,
        quantity=tx.quantity,
        price=tx.price,
        fees=tx.fees,
        total=round(tx.quantity * tx.price + tx.fees, 4),
        date=tx.date,
        notes=tx.notes,
    )


async def update_transaction(
    transaction_id: int,
    data: TransactionRequest,
    user: User,
    db: AsyncSession,
) -> TransactionResponse:
    from app.models.asset import Asset

    result = await db.execute(
        select(Transaction, Asset)
        .join(Asset, Transaction.asset_id == Asset.id)
        .where(
            Transaction.id == transaction_id,
            Transaction.user_id == user.id,
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tx, asset = row

    # Revert the effect of the old transaction on holdings before applying update
    await _revert_holdings(
        user_id=user.id,
        asset_id=tx.asset_id,
        tx_type=tx.type,
        quantity=tx.quantity,
        price=tx.price,
        db=db,
    )

    # Update transaction fields
    tx.type = data.type
    tx.quantity = data.quantity
    tx.price = data.price
    tx.fees = data.fees
    tx.date = data.date
    tx.notes = data.notes

    db.add(tx)
    await db.flush()

    # Apply the updated transaction to holdings
    await _update_holdings(
        user_id=user.id,
        asset_id=tx.asset_id,
        tx_type=data.type,
        quantity=data.quantity,
        price=data.price,
        db=db,
    )

    # Invalidate portfolio cache — holdings have changed
    await invalidate_portfolio_cache(user.id)

    return TransactionResponse(
        id=tx.id,
        asset_id=tx.asset_id,
        symbol=asset.symbol,
        type=tx.type,
        quantity=tx.quantity,
        price=tx.price,
        fees=tx.fees,
        total=round(tx.quantity * tx.price + tx.fees, 4),
        date=tx.date,
        notes=tx.notes,
    )


async def delete_transaction(
    transaction_id: int,
    user: User,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user.id,
        )
    )
    tx = result.scalar_one_or_none()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Revert the effect on holdings before deleting
    await _revert_holdings(
        user_id=user.id,
        asset_id=tx.asset_id,
        tx_type=tx.type,
        quantity=tx.quantity,
        price=tx.price,
        db=db,
    )

    await db.delete(tx)
    await db.flush()

    # Invalidate portfolio cache — holdings have changed
    await invalidate_portfolio_cache(user.id)


# ------------------------------------------------------------------
# Private helpers — holdings logic
# ------------------------------------------------------------------

async def _get_asset_by_id(asset_id: int, db: AsyncSession):
    from app.models.asset import Asset
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    return result.scalar_one_or_none()


async def _update_holdings(
    user_id: int,
    asset_id: int,
    tx_type: str,
    quantity: float,
    price: float,
    db: AsyncSession,
) -> None:
    """
    Applies a BUY or SELL transaction to the corresponding holding.
    BUY: creates or updates holding using weighted average price.
    SELL: reduces holding quantity, deletes if quantity reaches zero.
    """
    result = await db.execute(
        select(Holdings).where(
            Holdings.user_id == user_id,
            Holdings.asset_id == asset_id,
        )
    )
    holding = result.scalar_one_or_none()

    if tx_type == "BUY":
        if holding:
            # Recalculate avg_price using weighted average
            total_qty = holding.quantity + quantity
            holding.avg_price = (
                (holding.quantity * holding.avg_price) + (quantity * price)
            ) / total_qty
            holding.quantity = total_qty
            db.add(holding)
        else:
            db.add(Holdings(
                user_id=user_id,
                asset_id=asset_id,
                quantity=quantity,
                avg_price=price,
            ))

    elif tx_type == "SELL":
        if not holding or holding.quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient holdings to sell"
            )
        holding.quantity -= quantity
        if holding.quantity == 0:
            await db.delete(holding)
        else:
            db.add(holding)

    await db.flush()


async def _revert_holdings(
    user_id: int,
    asset_id: int,
    tx_type: str,
    quantity: float,
    price: float,
    db: AsyncSession,
) -> None:
    """
    Reverts the effect of a transaction on holdings.
    Used before updating or deleting a transaction to restore
    holdings to their previous state before applying the new values.
    """
    # Invert the original operation to undo its effect
    reverse_type = "SELL" if tx_type == "BUY" else "BUY"
    await _update_holdings(user_id, asset_id, reverse_type, quantity, price, db)