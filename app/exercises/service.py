"""Exercise business logic - validation and attempt handling."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise, ExerciseAttempt


def validate_answer(exercise: Exercise, user_answer: dict) -> bool:
    """Check if user answer is correct based on exercise content."""
    correct = exercise.content.get("correct_answer")
    if correct is None:
        return False
    user_val = user_answer.get("answer")
    if isinstance(correct, list):
        return user_val in correct or set(user_val or []) == set(correct)
    return user_val == correct


async def submit_attempt(
    db: AsyncSession,
    user_id: int,
    exercise_id: int,
    user_answer: dict,
) -> tuple[ExerciseAttempt, bool]:
    """Submit exercise attempt, return (attempt, is_correct)."""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise ValueError("Exercise not found")
    is_correct = validate_answer(exercise, user_answer)
    attempt = ExerciseAttempt(
        user_id=user_id,
        exercise_id=exercise_id,
        user_answer=user_answer,
        is_correct=is_correct,
    )
    db.add(attempt)
    await db.flush()
    await db.refresh(attempt)
    return attempt, is_correct
