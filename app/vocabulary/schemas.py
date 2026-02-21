"""Vocabulary schemas."""
from datetime import datetime
from pydantic import BaseModel


class VocabularyBase(BaseModel):
    word_kz: str
    translation_ru: str
    transcription: str | None = None
    example_sentence: str | None = None


class VocabularyCreate(VocabularyBase):
    pass


class VocabularyRead(VocabularyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserVocabularyAdd(BaseModel):
    vocabulary_id: int | None = None  # existing word
    word_kz: str | None = None  # or create new
    translation_ru: str | None = None
    transcription: str | None = None
    example_sentence: str | None = None


class UserVocabularyRead(BaseModel):
    id: int
    vocabulary_id: int
    word_kz: str
    translation_ru: str
    transcription: str | None
    status: str
    mastery: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class GameNextResponse(BaseModel):
    mode: str  # flashcard, reverse, multiple_choice
    vocab_id: int
    user_vocab_id: int
    prompt: str
    options: list[str] | None = None
    expected_language: str


class GameAnswerRequest(BaseModel):
    vocab_id: int
    mode: str
    user_answer: str


class GameAnswerResponse(BaseModel):
    is_correct: bool
    mastery: int
    status: str
    correct_answer: str | None = None


class UserVocabularyUpdate(BaseModel):
    status: str  # in_progress, learned
