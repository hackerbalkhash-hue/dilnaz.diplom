"""Vocabulary API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.vocabulary import Vocabulary, UserVocabulary
from app.vocabulary.schemas import (
    UserVocabularyAdd,
    UserVocabularyRead,
    UserVocabularyUpdate,
    GameAnswerRequest,
    GameAnswerResponse,
)
from app.vocabulary.service import add_word_to_user
from app.vocabulary.game_service import get_next_question, submit_answer

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("/", response_model=list[UserVocabularyRead])
async def list_my_vocabulary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = None,
):
    """List current user's vocabulary."""
    q = (
        select(UserVocabulary, Vocabulary)
        .join(Vocabulary, UserVocabulary.vocabulary_id == Vocabulary.id)
        .where(UserVocabulary.user_id == current_user.id)
    )
    if status_filter:
        q = q.where(UserVocabulary.status == status_filter)
    result = await db.execute(q)
    rows = result.all()
    out = []
    for uv, v in rows:
        out.append(
            UserVocabularyRead(
                id=uv.id,
                vocabulary_id=uv.vocabulary_id,
                word_kz=v.word_kz,
                translation_ru=v.translation_ru,
                transcription=v.transcription,
                status=uv.status,
                mastery=getattr(uv, "mastery", 0),
                created_at=uv.created_at,
            )
        )
    return out


@router.post("/", response_model=UserVocabularyRead)
async def add_word(
    data: UserVocabularyAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add word to personal vocabulary (manual or from existing)."""
    try:
        uv = await add_word_to_user(
            db,
            current_user.id,
            vocabulary_id=data.vocabulary_id,
            word_kz=data.word_kz,
            translation_ru=data.translation_ru,
            transcription=data.transcription,
            example_sentence=data.example_sentence,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    result = await db.execute(
        select(Vocabulary).where(Vocabulary.id == uv.vocabulary_id)
    )
    v = result.scalar_one()
    return UserVocabularyRead(
        id=uv.id,
        vocabulary_id=uv.vocabulary_id,
        word_kz=v.word_kz,
        translation_ru=v.translation_ru,
        transcription=v.transcription,
        status=uv.status,
        mastery=getattr(uv, "mastery", 0),
        created_at=uv.created_at,
    )


@router.get("/game/next")
async def game_next(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    last_vocab_id: int | None = Query(None, alias="last_vocab_id"),
):
    """Get next question for the vocabulary game."""
    payload = await get_next_question(db, current_user.id, last_vocab_id)
    if not payload:
        return {"question": None, "message": "No words to learn. Add words to your vocabulary first."}
    return {"question": payload}


@router.post("/game/answer", response_model=GameAnswerResponse)
async def game_submit_answer(
    data: GameAnswerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit answer for vocabulary game."""
    try:
        result = await submit_answer(
            db, current_user.id, data.vocab_id, data.mode, data.user_answer
        )
        return GameAnswerResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{user_vocab_id}")
async def update_status(
    user_vocab_id: int,
    data: UserVocabularyUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update word status (in_progress / learned)."""
    result = await db.execute(
        select(UserVocabulary).where(
            UserVocabulary.id == user_vocab_id,
            UserVocabulary.user_id == current_user.id,
        )
    )
    uv = result.scalar_one_or_none()
    if not uv:
        raise HTTPException(status_code=404, detail="Not found")
    uv.status = data.status
    await db.flush()
    return {"status": "ok"}


@router.delete("/{user_vocab_id}")
async def remove_word(
    user_vocab_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Remove word from personal vocabulary."""
    result = await db.execute(
        select(UserVocabulary).where(
            UserVocabulary.id == user_vocab_id,
            UserVocabulary.user_id == current_user.id,
        )
    )
    uv = result.scalar_one_or_none()
    if not uv:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(uv)
    return {"status": "ok"}
