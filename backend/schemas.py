from datetime import date, datetime

from pydantic import BaseModel, Field


class TransactionRequest(BaseModel):
    userId: str = Field(..., min_length=1, max_length=36, description="User UUID")
    amount: int = Field(..., gt=0, le=10000, description="Points to award (1-10000)")
    idempotencyKey: str = Field(..., min_length=1, max_length=100, description="Unique key to prevent duplicate processing")
    description: str | None = Field(None, max_length=255, description="Optional description")


class TransactionResponse(BaseModel):
    id: str
    userId: str
    amount: int
    idempotencyKey: str
    description: str | None
    createdAt: datetime
    duplicate: bool = False

    model_config = {"from_attributes": True}


class UserSummaryResponse(BaseModel):
    userId: str
    username: str
    totalPoints: int
    transactionCount: int
    consistencyScore: float
    activeDays: int
    firstTransactionDate: date | None
    lastTransactionDate: date | None
    memberSince: datetime

    model_config = {"from_attributes": True}


class RankingEntry(BaseModel):
    rank: int
    userId: str
    username: str
    totalPoints: int
    consistencyScore: float
    compositeScore: float


class RankingResponse(BaseModel):
    rankings: list[RankingEntry]
    total: int
    page: int
    limit: int


class ErrorResponse(BaseModel):
    detail: str
