"""File upload and content import/export."""
import csv
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.file import File
from app.models.lesson import Lesson
from app.models.exercise import Exercise
from app.models.vocabulary import Vocabulary

settings = get_settings()


def ensure_upload_dir() -> Path:
    """Ensure upload directory exists."""
    p = Path(settings.UPLOAD_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


async def save_upload(
    db: AsyncSession,
    filename: str,
    file_path: str,
    user_id: int | None = None,
    content_type: str | None = None,
    entity_type: str | None = None,
) -> File:
    """Save file metadata to DB."""
    f = File(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        content_type=content_type,
        entity_type=entity_type,
    )
    db.add(f)
    await db.flush()
    await db.refresh(f)
    return f


def parse_json_lessons(data: bytes) -> list[dict]:
    """Parse JSON for lessons import."""
    decoded = data.decode("utf-8")
    obj = json.loads(decoded)
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and "lessons" in obj:
        return obj["lessons"]
    return [obj]


def parse_csv_vocabulary(data: bytes) -> list[dict]:
    """Parse CSV for vocabulary import. Expected: word_kz,translation_ru[,transcription,example]"""
    decoded = data.decode("utf-8")
    reader = csv.DictReader(decoded.splitlines())
    return list(reader)
