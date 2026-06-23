import uuid
from datetime import date, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Transaction, User, UserStats
from schemas import TransactionRequest, TransactionResponse
from config import settings


async def create_transaction(
    db: AsyncSession, req: TransactionRequest
) -> TransactionResponse:
    # Check for duplicate idempotency key first (fast path)
    existing = await db.execute(
        select(Transaction).where(Transaction.idempotency_key == req.idempotencyKey)
    )
    existing_tx = existing.scalar_one_or_none()
    if existing_tx:
        return TransactionResponse(
            id=existing_tx.id,
            userId=existing_tx.user_id,
            amount=existing_tx.amount,
            idempotencyKey=existing_tx.idempotency_key,
            description=existing_tx.description,
            createdAt=existing_tx.created_at,
            duplicate=True,
        )

    # Verify user exists (create if not — auto-registration for demo simplicity)
    user_result = await db.execute(select(User).where(User.id == req.userId))
    user = user_result.scalar_one_or_none()
    if not user:
        user = User(id=req.userId, username=f"user_{req.userId[:8]}")
        db.add(user)
        await db.flush()

    # Create the transaction
    tx = Transaction(
        id=str(uuid.uuid4()),
        user_id=req.userId,
        amount=req.amount,
        idempotency_key=req.idempotencyKey,
        description=req.description,
    )
    db.add(tx)

    # Atomic update of user_stats with row-level locking
    today = date.today()
    stats_result = await db.execute(
        select(UserStats)
        .where(UserStats.user_id == req.userId)
        .with_for_update()
    )
    stats = stats_result.scalar_one_or_none()

    if stats is None:
        stats = UserStats(
            user_id=req.userId,
            total_points=req.amount,
            transaction_count=1,
            distinct_days=1,
            first_transaction_date=today,
            last_transaction_date=today,
        )
        db.add(stats)
    else:
        # Check if this transaction is on a new day
        is_new_day = stats.last_transaction_date != today
        stats.total_points += req.amount
        stats.transaction_count += 1
        if is_new_day:
            stats.distinct_days += 1
        stats.last_transaction_date = today
        if stats.first_transaction_date is None:
            stats.first_transaction_date = today

    await db.commit()
    await db.refresh(tx)

    return TransactionResponse(
        id=tx.id,
        userId=tx.user_id,
        amount=tx.amount,
        idempotencyKey=tx.idempotency_key,
        description=tx.description,
        createdAt=tx.created_at,
        duplicate=False,
    )
