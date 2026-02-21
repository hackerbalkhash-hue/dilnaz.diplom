"""Content import/export API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, RequireTeacher
from app.models.user import User
from app.models.lesson import Lesson
from app.models.vocabulary import Vocabulary
from app.files.service import ensure_upload_dir, save_upload, parse_json_lessons, parse_csv_vocabulary

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/import/lessons")
async def import_lessons(
    file: UploadFile,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Import lessons from JSON file."""
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="JSON file required")
    data = await file.read()
    try:
        items = parse_json_lessons(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    created = 0
    for item in items:
        lesson = Lesson(
            title=item.get("title", "Untitled"),
            level=item.get("level", "A1"),
            topic=item.get("topic", ""),
            content=item.get("content", ""),
            order_index=item.get("order_index", 0),
        )
        db.add(lesson)
        created += 1
    await db.flush()
    return {"imported": created}


@router.post("/import/vocabulary")
async def import_vocabulary(
    file: UploadFile,
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Import vocabulary from CSV. Columns: word_kz, translation_ru, transcription?, example_sentence?"""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")
    data = await file.read()
    try:
        rows = parse_csv_vocabulary(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")
    created = 0
    for row in rows:
        word_kz = row.get("word_kz", "").strip()
        trans = row.get("translation_ru", "").strip()
        if not word_kz or not trans:
            continue
        v = Vocabulary(
            word_kz=word_kz,
            translation_ru=trans,
            transcription=row.get("transcription", "").strip() or None,
            example_sentence=row.get("example_sentence", "").strip() or None,
        )
        db.add(v)
        created += 1
    await db.flush()
    return {"imported": created}


@router.get("/export/lessons")
async def export_lessons(
    current_user: Annotated[User, RequireTeacher],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Export lessons as JSON."""
    result = await db.execute(select(Lesson).order_by(Lesson.order_index, Lesson.id))
    lessons = result.scalars().all()
    data = [
        {
            "title": l.title,
            "level": l.level,
            "topic": l.topic,
            "content": l.content,
            "order_index": l.order_index,
        }
        for l in lessons
    ]
    import json
    return {"lessons": data, "format": "json"}
