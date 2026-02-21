"""Progress and statistics API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.lesson import Lesson, LessonCompletion
from app.models.exercise import Exercise, ExerciseAttempt
from app.models.test import Test, TestAttempt
from app.models.vocabulary import UserVocabulary
from app.progress.schemas import ProgressSummary

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/summary", response_model=ProgressSummary)
async def get_progress_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get progress summary for current user."""
    total_lessons = (await db.execute(select(func.count(Lesson.id)))).scalar() or 0
    completed = (
        await db.execute(
            select(func.count(LessonCompletion.id)).where(
                LessonCompletion.user_id == current_user.id
            )
        )
    ).scalar() or 0

    ex_total = (
        await db.execute(
            select(func.count(ExerciseAttempt.id)).where(
                ExerciseAttempt.user_id == current_user.id
            )
        )
    ).scalar() or 0
    ex_correct = (
        await db.execute(
            select(func.count(ExerciseAttempt.id)).where(
                ExerciseAttempt.user_id == current_user.id,
                ExerciseAttempt.is_correct == True,
            )
        )
    ).scalar() or 0

    test_total = (
        await db.execute(
            select(func.count(TestAttempt.id)).where(
                TestAttempt.user_id == current_user.id
            )
        )
    ).scalar() or 0
    test_passed = (
        await db.execute(
            select(func.count(TestAttempt.id)).where(
                TestAttempt.user_id == current_user.id,
                TestAttempt.passed == True,
            )
        )
    ).scalar() or 0

    vocab_total = (
        await db.execute(
            select(func.count(UserVocabulary.id)).where(
                UserVocabulary.user_id == current_user.id
            )
        )
    ).scalar() or 0
    vocab_learned = (
        await db.execute(
            select(func.count(UserVocabulary.id)).where(
                UserVocabulary.user_id == current_user.id,
                UserVocabulary.status == "learned",
            )
        )
    ).scalar() or 0

    return ProgressSummary(
        completed_lessons=completed,
        total_lessons=total_lessons,
        exercise_attempts=ex_total,
        exercise_correct=ex_correct,
        test_attempts=test_total,
        test_passed=test_passed,
        vocabulary_size=vocab_total,
        vocabulary_learned=vocab_learned,
    )
