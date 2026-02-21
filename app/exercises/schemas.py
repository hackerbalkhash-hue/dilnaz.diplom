"""Exercise schemas."""
from datetime import datetime
from pydantic import BaseModel


class ExerciseBase(BaseModel):
    title: str
    exercise_type: str  # multiple_choice, fill_blank, matching
    content: dict  # question, options, correct_answer, etc.
    order_index: int = 0
    retry_allowed: bool = True


class ExerciseCreate(ExerciseBase):
    lesson_id: int


class ExerciseUpdate(BaseModel):
    title: str | None = None
    exercise_type: str | None = None
    content: dict | None = None
    order_index: int | None = None
    retry_allowed: bool | None = None


class ExerciseRead(ExerciseBase):
    id: int
    lesson_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExerciseAttemptSubmit(BaseModel):
    user_answer: dict


class ExerciseAttemptRead(BaseModel):
    id: int
    exercise_id: int
    is_correct: bool
    created_at: datetime

    class Config:
        from_attributes = True
