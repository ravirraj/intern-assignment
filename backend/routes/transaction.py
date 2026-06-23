from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import ErrorResponse, TransactionRequest, TransactionResponse
from services.transaction_service import create_transaction

router = APIRouter()


@router.post(
    "/transaction",
    response_model=TransactionResponse,
    responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
    status_code=201,
)
async def submit_transaction(req: TransactionRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await create_transaction(db, req)
        return result
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
