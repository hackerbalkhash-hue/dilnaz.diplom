"""
Test, questions, and attempts models.
"""
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Test(Base):
    """Test linked to a lesson."""

    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    passing_score: Mapped[float] = mapped_column(Float, default=70.0)
    is_final: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TestQuestion(Base):
    """Question in a test."""

    __tablename__ = "test_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tests.id", ondelete="CASCADE")
    )
    question_text: Mapped[str] = mapped_column(Text)
    # JSON: type, options, correct_answer, points
    content: Mapped[dict] = mapped_column(JSON)
    order_index: Mapped[int] = mapped_column(Integer, default=0)


class TestAttempt(Base):
    """Student attempt on a test."""

    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    test_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tests.id", ondelete="CASCADE")
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(nullable=True)  # None = incomplete
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class TestAttemptAnswer(Base):
    """Answer to a question in a test attempt."""

    __tablename__ = "test_attempt_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_attempt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("test_attempts.id", ondelete="CASCADE")
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("test_questions.id", ondelete="CASCADE")
    )
    user_answer: Mapped[dict] = mapped_column(JSON)
    is_correct: Mapped[bool | None] = mapped_column(nullable=True)
    points_earned: Mapped[float | None] = mapped_column(Float, nullable=True)
