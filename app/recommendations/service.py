"""Rule-based recommendation engine."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation


async def create_recommendation(
    db: AsyncSession,
    user_id: int,
    rec_type: str,
    title: str,
    description: str | None = None,
    target_lesson_id: int | None = None,
    target_exercise_id: int | None = None,
) -> Recommendation:
    """Create recommendation for user."""
    rec = Recommendation(
        user_id=user_id,
        recommendation_type=rec_type,
        title=title,
        description=description,
        target_lesson_id=target_lesson_id,
        target_exercise_id=target_exercise_id,
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec
