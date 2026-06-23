from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import RankingResponse
from services.ranking_service import get_ranking

router = APIRouter()


@router.get("/ranking", response_model=RankingResponse)
async def ranking(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
):
    return await get_ranking(db, page=page, limit=limit)
