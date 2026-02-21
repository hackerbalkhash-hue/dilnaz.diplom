"""Progress schemas."""
from pydantic import BaseModel


class ProgressSummary(BaseModel):
    completed_lessons: int
    total_lessons: int
    exercise_attempts: int
    exercise_correct: int
    test_attempts: int
    test_passed: int
    vocabulary_size: int
    vocabulary_learned: int
