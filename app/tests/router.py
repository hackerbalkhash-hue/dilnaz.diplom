"""Test API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, RequireTeacher
from app.models.user import User
from app.models.test import Test, TestQuestion, TestAttempt, TestAttemptAnswer
from app.models.lesson import Lesson
from app.lessons.service import get_completed_lesson_ids, get_prerequisites_map, lesson_is_accessible
from app.tests.schemas import (
    TestCreate,
    TestUpdate,
    TestRead,
    TestQuestionRead,
    TestAttemptRead,
    TestAttemptSubmit,
)
from app.tests.service import start_attempt, submit_test

router = APIRouter(prefix="/tests", tags=["tests"])


async def _check_lesson_access(db, user, lesson_id):
    if user.role.value != "student":
        return True
    completed = await get_completed_lesson_ids(db, user.id)
    prereq_map = await get_prerequisites_map(db)
    return lesson_is_accessible(lesson_id, completed, prereq_map)[0]


@router.get("/", response_model=list[TestRead])
async def list_tests(
    lesson_id: int | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List tests, optionally by lesson."""
    q = select(Test).order_by(Test.id)
    if lesson_id:
        q = q.where(Test.lesson_id == lesson_id)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{test_id}", response_model=TestRead)
async def get_test(
    test_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get test by ID."""
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if current_user.role.value == "student":
        ok = await _check_lesson_access(db, current_user, test.lesson_id)
        if not ok:
            raise HTTPException(
                status_code=403,
                detail="Complete lesson prerequisites first",
            )
    return test


@router.get("/{test_id}/questions", response_model=list[TestQuestionRead])
async def get_test_questions(
    test_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get test questions."""
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if current_user.role.value == "student":
        ok = await _check_lesson_access(db, current_user, test.lesson_id)
        if not ok:
            raise HTTPException(status_code=403, detail="Complete lesson first")
    q_res = await db.execute(
        select(TestQuestion).where(TestQuestion.test_id == test_id).order_by(TestQuestion.order_index)
    )
    return list(q_res.scalars().all())


@router.post("/{test_id}/attempt")
async def start_test_attempt(
    test_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Start new test attempt."""
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    ok = await _check_lesson_access(db, current_user, test.lesson_id)
    if not ok:
        raise HTTPException(status_code=403, detail="Complete lesson first")
    attempt = await start_attempt(db, current_user.id, test_id)
    return {"attempt_id": attempt.id}


@router.post("/attempts/{attempt_id}/submit")
async def submit_test_attempt(
    attempt_id: int,
    data: TestAttemptSubmit,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit test attempt with answers."""
    answers = [
        {"question_id": a.question_id, "user_answer": a.user_answer}
        for a in data.answers
    ]
    try:
        attempt = await submit_test(db, attempt_id, current_user.id, answers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "score": attempt.score,
        "passed": attempt.passed,
    }


@router.get("/attempts/{attempt_id}")
async def get_attempt(
    attempt_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get attempt details (for review)."""
    result = await db.execute(
        select(TestAttempt).where(
            TestAttempt.id == attempt_id,
            TestAttempt.user_id == current_user.id,
        )
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    answers_result = await db.execute(
        select(TestAttemptAnswer).where(
            TestAttemptAnswer.test_attempt_id == attempt_id
        )
    )
    answers = list(answers_result.scalars().all())
    return {
        "attempt": TestAttemptRead.model_validate(attempt),
        "answers": [{"question_id": a.question_id, "is_correct": a.is_correct} for a in answers],
    }


# Teacher only
@router.post("/", response_model=TestRead)
async def create_test(
    data: TestCreate,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create test (teacher/admin)."""
    test = Test(
        lesson_id=data.lesson_id,
        title=data.title,
        description=data.description,
        passing_score=data.passing_score,
    )
    db.add(test)
    await db.flush()
    await db.refresh(test)
    return test


@router.put("/{test_id}", response_model=TestRead)
async def update_test(
    test_id: int,
    data: TestUpdate,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update test (teacher/admin)."""
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if data.title is not None:
        test.title = data.title
    if data.description is not None:
        test.description = data.description
    if data.passing_score is not None:
        test.passing_score = data.passing_score
    await db.flush()
    await db.refresh(test)
    return test


@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete test (teacher/admin)."""
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    await db.delete(test)
    return {"status": "ok"}
