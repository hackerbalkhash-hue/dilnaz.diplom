"""Exercise API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, RequireTeacher
from app.models.user import User
from app.models.exercise import Exercise, ExerciseAttempt
from app.lessons.service import get_completed_lesson_ids, get_prerequisites_map, lesson_is_accessible
from app.models.lesson import Lesson
from app.exercises.schemas import (
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseRead,
    ExerciseAttemptSubmit,
    ExerciseAttemptRead,
)
from app.exercises.service import submit_attempt

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=list[ExerciseRead])
async def list_exercises(
    lesson_id: int | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List exercises, optionally by lesson."""
    q = select(Exercise).order_by(Exercise.order_index, Exercise.id)
    if lesson_id:
        q = q.where(Exercise.lesson_id == lesson_id)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{exercise_id}", response_model=ExerciseRead)
async def get_exercise(
    exercise_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get exercise by ID. Student must have completed lesson prerequisites."""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if current_user.role.value == "student":
        lesson_res = await db.execute(
            select(Lesson).where(Lesson.id == exercise.lesson_id)
        )
        lesson = lesson_res.scalar_one_or_none()
        if lesson:
            completed = await get_completed_lesson_ids(db, current_user.id)
            prereq_map = await get_prerequisites_map(db)
            accessible, _ = lesson_is_accessible(
                lesson.id, completed, prereq_map
            )
            if not accessible:
                raise HTTPException(
                    status_code=403,
                    detail="Complete lesson prerequisites first",
                )
    return exercise


@router.post("/{exercise_id}/attempt")
async def submit_exercise_attempt(
    exercise_id: int,
    data: ExerciseAttemptSubmit,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit exercise attempt. Returns correctness feedback."""
    try:
        attempt, is_correct = await submit_attempt(
            db, current_user.id, exercise_id, data.user_answer
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "attempt_id": attempt.id,
        "is_correct": is_correct,
    }


# Teacher only
@router.post("/", response_model=ExerciseRead)
async def create_exercise(
    data: ExerciseCreate,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create exercise (teacher/admin)."""
    exercise = Exercise(
        lesson_id=data.lesson_id,
        title=data.title,
        exercise_type=data.exercise_type,
        content=data.content,
        order_index=data.order_index,
        retry_allowed=data.retry_allowed,
    )
    db.add(exercise)
    await db.flush()
    await db.refresh(exercise)
    return exercise


@router.put("/{exercise_id}", response_model=ExerciseRead)
async def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update exercise (teacher/admin)."""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if data.title is not None:
        exercise.title = data.title
    if data.exercise_type is not None:
        exercise.exercise_type = data.exercise_type
    if data.content is not None:
        exercise.content = data.content
    if data.order_index is not None:
        exercise.order_index = data.order_index
    if data.retry_allowed is not None:
        exercise.retry_allowed = data.retry_allowed
    await db.flush()
    await db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}")
async def delete_exercise(
    exercise_id: int,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete exercise (teacher/admin)."""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    await db.delete(exercise)
    return {"status": "ok"}
