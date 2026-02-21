"""
Exercise and exercise attempts models.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExerciseType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"


class Exercise(Base):
    """Exercise linked to a lesson."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    exercise_type: Mapped[str] = mapped_column(String(50))
    # JSON: question, options, correct_answer, etc.
    content: Mapped[dict] = mapped_column(JSON)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    retry_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ExerciseAttempt(Base):
    """Student attempt on an exercise."""

    __tablename__ = "exercise_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exercises.id", ondelete="CASCADE")
    )
    user_answer: Mapped[dict] = mapped_column(JSON)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
