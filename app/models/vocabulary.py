"""
Vocabulary and user vocabulary models.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VocabularyStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    LEARNED = "learned"


class Vocabulary(Base):
    """Dictionary entry (word/phrase)."""

    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word_kz: Mapped[str] = mapped_column(String(255))
    translation_ru: Mapped[str] = mapped_column(String(255))
    transcription: Mapped[str | None] = mapped_column(String(255), nullable=True)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class UserVocabulary(Base):
    """User's personal vocabulary with status and mastery."""

    __tablename__ = "user_vocabulary"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    vocabulary_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vocabulary.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50), default="in_progress")
    mastery: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    source: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # manual, suggestion
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("user_id", "vocabulary_id", name="uq_user_vocab"),
    )
