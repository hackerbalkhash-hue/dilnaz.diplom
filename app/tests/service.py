"""Test business logic - evaluation and attempt handling."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test import Test, TestQuestion, TestAttempt, TestAttemptAnswer
from app.models.lesson import LessonCompletion


async def start_attempt(db: AsyncSession, user_id: int, test_id: int) -> TestAttempt:
    """Start a new test attempt."""
    attempt = TestAttempt(user_id=user_id, test_id=test_id)
    db.add(attempt)
    await db.flush()
    await db.refresh(attempt)
    return attempt


def evaluate_question(question: TestQuestion, user_answer: dict) -> tuple[bool, float]:
    """Evaluate single question. Returns (is_correct, points_earned)."""
    content = question.content or {}
    correct = content.get("correct_answer")
    points = content.get("points", 1.0)
    user_val = user_answer.get("answer")
    if correct is None:
        return False, 0.0
    is_correct = user_val == correct
    return is_correct, points if is_correct else 0.0


async def submit_test(
    db: AsyncSession,
    attempt_id: int,
    user_id: int,
    answers: list[dict],
) -> TestAttempt:
    """Submit test with answers, compute score, complete attempt."""
    result = await db.execute(
        select(TestAttempt).where(
            TestAttempt.id == attempt_id,
            TestAttempt.user_id == user_id,
        )
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise ValueError("Attempt not found")
    if attempt.completed_at:
        raise ValueError("Attempt already completed")

    questions_result = await db.execute(
        select(TestQuestion).where(TestQuestion.test_id == attempt.test_id)
    )
    questions = {q.id: q for q in questions_result.scalars().all()}

    total_points = 0.0
    earned_points = 0.0
    for ans in answers:
        qid = ans.get("question_id")
        user_ans = ans.get("user_answer", {})
        q = questions.get(qid)
        if not q:
            continue
        is_correct, pts = evaluate_question(q, user_ans)
        max_pts = (q.content or {}).get("points", 1.0)
        total_points += max_pts
        earned_points += pts
        db.add(
            TestAttemptAnswer(
                test_attempt_id=attempt_id,
                question_id=qid,
                user_answer=user_ans,
                is_correct=is_correct,
                points_earned=pts,
            )
        )

    test_result = await db.execute(select(Test).where(Test.id == attempt.test_id))
    test = test_result.scalar_one_or_none()
    passing = test.passing_score if test else 70.0
    score = (earned_points / total_points * 100) if total_points > 0 else 0
    passed = score >= passing

    attempt.score = round(score, 2)
    attempt.passed = passed
    attempt.completed_at = datetime.utcnow()
    await db.flush()

    # Auto-complete lesson when user passes final test
    if passed and test and getattr(test, "is_final", False):
        existing = await db.execute(
            select(LessonCompletion).where(
                LessonCompletion.user_id == user_id,
                LessonCompletion.lesson_id == test.lesson_id,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(LessonCompletion(user_id=user_id, lesson_id=test.lesson_id))
            await db.flush()

    await db.refresh(attempt)
    return attempt
