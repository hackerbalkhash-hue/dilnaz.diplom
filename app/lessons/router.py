"""Lesson API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, RequireTeacher
from app.models.user import User
from app.models.lesson import Lesson, LessonPrerequisite
from app.models.test import Test, TestAttempt
from app.lessons.schemas import LessonCreate, LessonUpdate, LessonRead, LessonWithAccess
from app.lessons.service import (
    get_completed_lesson_ids,
    get_prerequisites_map,
    lesson_is_accessible,
    get_next_lesson,
    create_lesson,
    update_lesson,
    complete_lesson,
)

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/", response_model=list[LessonWithAccess])
async def list_lessons(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List lessons with access status for current user."""
    result = await db.execute(
        select(Lesson).order_by(Lesson.order_index, Lesson.id)
    )
    lessons = result.scalars().all()
    completed = await get_completed_lesson_ids(db, current_user.id)
    prereq_map = await get_prerequisites_map(db)
    out = []
    for les in lessons:
        accessible, prereqs = lesson_is_accessible(les.id, completed, prereq_map)
        out.append(
            LessonWithAccess(
                id=les.id,
                title=les.title,
                level=les.level,
                topic=les.topic,
                content=les.content,
                order_index=les.order_index,
                created_at=les.created_at,
                is_locked=not accessible,
                prerequisite_lesson_ids=prereqs,
            )
        )
    return out


@router.get("/{lesson_id}/next")
async def get_next_lesson_route(
    lesson_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get next lesson in curriculum. Returns next_lesson_id, title, level, is_accessible, locked_reason."""
    completed = await get_completed_lesson_ids(db, current_user.id)
    prereq_map = await get_prerequisites_map(db)
    next_info = await get_next_lesson(db, lesson_id, completed, prereq_map)
    if not next_info:
        return {"next_lesson_id": None, "title": None, "level": None, "is_accessible": False, "locked_reason": None}
    return next_info


@router.get("/{lesson_id}", response_model=LessonWithAccess)
async def get_lesson(
    lesson_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get lesson by ID. Returns 403 if prerequisites not met."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    completed = await get_completed_lesson_ids(db, current_user.id)
    prereq_map = await get_prerequisites_map(db)
    accessible, prereqs = lesson_is_accessible(lesson_id, completed, prereq_map)
    if not accessible:
        raise HTTPException(
            status_code=403,
            detail="Complete prerequisite lessons first",
        )
    return LessonWithAccess(
        id=lesson.id,
        title=lesson.title,
        level=lesson.level,
        topic=lesson.topic,
        content=lesson.content,
        order_index=lesson.order_index,
        created_at=lesson.created_at,
        is_locked=False,
        prerequisite_lesson_ids=prereqs,
    )


@router.post("/{lesson_id}/complete")
async def mark_complete(
    lesson_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark lesson as completed. Requires passing the final test if one exists."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lesson not found")
    completed = await get_completed_lesson_ids(db, current_user.id)
    prereq_map = await get_prerequisites_map(db)
    accessible, _ = lesson_is_accessible(lesson_id, completed, prereq_map)
    if not accessible:
        raise HTTPException(
            status_code=403,
            detail="Complete prerequisite lessons first",
        )
    # If lesson has final test, require passing it
    test_result = await db.execute(
        select(Test).where(Test.lesson_id == lesson_id, Test.is_final == True)
    )
    final_test = test_result.scalar_one_or_none()
    if final_test:
        passed_result = await db.execute(
            select(TestAttempt).where(
                TestAttempt.test_id == final_test.id,
                TestAttempt.user_id == current_user.id,
                TestAttempt.passed == True,
            )
        )
        if not passed_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Pass the final test to complete this lesson (≥70%)",
            )
    await complete_lesson(db, current_user.id, lesson_id)
    return {"status": "ok"}


# Teacher/Admin only
@router.post("/", response_model=LessonRead)
async def create_lesson_route(
    data: LessonCreate,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create lesson (teacher/admin)."""
    lesson = await create_lesson(db, data)
    return lesson


@router.put("/{lesson_id}", response_model=LessonRead)
async def update_lesson_route(
    lesson_id: int,
    data: LessonUpdate,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update lesson (teacher/admin)."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return await update_lesson(db, lesson, data)


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete lesson (teacher/admin)."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    await db.delete(lesson)
    return {"status": "ok"}
