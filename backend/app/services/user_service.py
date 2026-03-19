from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.user import User
from app.models.holdings import Holdings
from app.models.transaction import Transaction
from app.schemas.users import UserResponse, UserUpdateRequest


async def get_me(user: User) -> UserResponse:
    return UserResponse.model_validate(user)

async def update_me(
        user: User,
        data: UserUpdateRequest,
        db: AsyncSession,
) -> UserResponse:
    # Only update the fields that come in the request
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.risk_profile is not None:
        user.risk_profile = data.risk_profile

    db.add(user)
    await db.flush()
    return UserResponse.model_validate(user)

async def delete_me( user: User, db: AsyncSession) -> None:
    await db.delete(user)
    await db.flush()

async def get_my_stats( user: User, db: AsyncSession) -> dict:
    # Get total transactions
    tx_count = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == user.id
        )
    )
    total_transactions = tx_count.scalar() or 0

    # Total of holdings
    holdings_count = await db.execute(
        select(func.count(Holdings.id)).where(
            Holdings.user_id == user.id
        )
    )
    total_holdings = holdings_count.scalar() or 0

    # Total invested amount
    invested = await db.execute(
        select(func.sum(Holdings.quantity * Holdings.avg_price)).where(
            Holdings.user_id == user.id
        )
    )
    total_invested = invested.scalar() or 0.0

    return {
        "user_id": user.id,
        "total_transactions": total_transactions,
        "total_holdings": total_holdings,
        "total_invested": round(total_invested, 2),
        "risk_profile": user.risk_profile,
        "member_since": user.created_at,
    }