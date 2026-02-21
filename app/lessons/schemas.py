"""Lesson schemas."""
from datetime import datetime
from pydantic import BaseModel


class LessonBase(BaseModel):
    title: str
    level: str  # A1, A2, B1
    topic: str
    content: str
    order_index: int = 0


class LessonCreate(LessonBase):
    prerequisite_ids: list[int] = []


class LessonUpdate(BaseModel):
    title: str | None = None
    level: str | None = None
    topic: str | None = None
    content: str | None = None
    order_index: int | None = None
    prerequisite_ids: list[int] | None = None


class LessonRead(LessonBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LessonWithAccess(LessonRead):
    """Lesson with access status for student."""
    is_locked: bool
    prerequisite_lesson_ids: list[int] = []
