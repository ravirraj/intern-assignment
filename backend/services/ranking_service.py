from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, UserStats
from schemas import RankingEntry, RankingResponse, UserSummaryResponse
from config import settings


def compute_consistency_score(distinct_days: int, first_date: date | None, last_date: date | None) -> float:
    if not first_date or not last_date:
        return 0.0
    total_days = (last_date - first_date).days + 1
    if total_days <= 0:
        return 0.0
    return round(min(distinct_days / total_days, 1.0), 4)


def compute_composite_score(total_points: int, consistency_score: float) -> float:
    return round(
        total_points * settings.RANKING_WEIGHT_POINTS
        + consistency_score * 1000 * settings.RANKING_WEIGHT_CONSISTENCY,
        2,
    )


async def get_user_summary(db: AsyncSession, user_id: str) -> UserSummaryResponse | None:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return None

    stats_result = await db.execute(select(UserStats).where(UserStats.user_id == user_id))
    stats = stats_result.scalar_one_or_none()

    if not stats:
        return UserSummaryResponse(
            userId=user.id,
            username=user.username,
            totalPoints=0,
            transactionCount=0,
            consistencyScore=0.0,
            activeDays=0,
            firstTransactionDate=None,
            lastTransactionDate=None,
            memberSince=user.created_at,
        )

    consistency = compute_consistency_score(
        stats.distinct_days, stats.first_transaction_date, stats.last_transaction_date
    )

    return UserSummaryResponse(
        userId=user.id,
        username=user.username,
        totalPoints=stats.total_points,
        transactionCount=stats.transaction_count,
        consistencyScore=consistency,
        activeDays=stats.distinct_days,
        firstTransactionDate=stats.first_transaction_date,
        lastTransactionDate=stats.last_transaction_date,
        memberSince=user.created_at,
    )


async def get_ranking(db: AsyncSession, page: int = 1, limit: int = 20) -> RankingResponse:
    offset = (page - 1) * limit

    # Get total count of users with stats
    count_result = await db.execute(select(func.count(UserStats.user_id)))
    total = count_result.scalar() or 0

    # Fetch all user stats sorted by composite score (computed in Python for correctness)
    stats_result = await db.execute(
        select(UserStats, User.username)
        .join(User, UserStats.user_id == User.id)
        .order_by(UserStats.total_points.desc())
    )
    all_stats = stats_result.all()

    # Compute composite scores and rank
    scored: list[tuple[int, str, str, int, float, float]] = []
    for stats_row, username in all_stats:
        consistency = compute_consistency_score(
            stats_row.distinct_days, stats_row.first_transaction_date, stats_row.last_transaction_date
        )
        composite = compute_composite_score(stats_row.total_points, consistency)
        scored.append((
            0,  # placeholder rank
            stats_row.user_id,
            username,
            stats_row.total_points,
            consistency,
            composite,
        ))

    # Sort by composite score descending, then by total_points descending as tiebreaker
    scored.sort(key=lambda x: (-x[5], -x[3]))

    # Assign ranks
    rankings = []
    for i, (_, user_id, username, total_pts, consistency, composite) in enumerate(scored[offset:offset + limit], start=offset + 1):
        rankings.append(RankingEntry(
            rank=i,
            userId=user_id,
            username=username,
            totalPoints=total_pts,
            consistencyScore=consistency,
            compositeScore=composite,
        ))

    return RankingResponse(
        rankings=rankings,
        total=total,
        page=page,
        limit=limit,
    )
