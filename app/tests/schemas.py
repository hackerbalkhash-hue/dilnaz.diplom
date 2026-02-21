"""Test schemas."""
from datetime import datetime
from pydantic import BaseModel


class TestBase(BaseModel):
    title: str
    description: str | None = None
    passing_score: float = 70.0


class TestCreate(TestBase):
    lesson_id: int


class TestUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    passing_score: float | None = None


class TestRead(TestBase):
    id: int
    lesson_id: int
    is_final: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class TestQuestionRead(BaseModel):
    id: int
    test_id: int
    question_text: str
    content: dict
    order_index: int

    class Config:
        from_attributes = True


class TestAttemptStart(BaseModel):
    pass


class TestAttemptAnswerSubmit(BaseModel):
    question_id: int
    user_answer: dict


class TestAttemptSubmit(BaseModel):
    answers: list[TestAttemptAnswerSubmit]


class TestAttemptRead(BaseModel):
    id: int
    test_id: int
    score: float | None
    passed: bool | None
    started_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
