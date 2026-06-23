from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import ErrorResponse, UserSummaryResponse
from services.ranking_service import get_user_summary

router = APIRouter()


@router.get(
    "/summary/{userId}",
    response_model=UserSummaryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def user_summary(userId: str, db: AsyncSession = Depends(get_db)):
    result = await get_user_summary(db, userId)
    if not result:
        raise HTTPException(status_code=404, detail=f"User {userId} not found")
    return result
