"""
File storage model - for import/export and uploads.
"""
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class File(Base):
    """File metadata stored in DB, file on filesystem."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # lessons, exercises, vocabulary
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
