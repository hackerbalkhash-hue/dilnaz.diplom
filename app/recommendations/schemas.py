"""Recommendation schemas."""
from datetime import datetime
from pydantic import BaseModel


class RecommendationRead(BaseModel):
    id: int
    recommendation_type: str
    title: str
    description: str | None
    target_lesson_id: int | None
    target_exercise_id: int | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
