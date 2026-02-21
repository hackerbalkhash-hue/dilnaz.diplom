"""Vocabulary game: spaced repetition, mastery, question selection."""
import random
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vocabulary import Vocabulary, UserVocabulary

MASTERY_LEARNED = 5
GAME_MODES = ["flashcard", "reverse", "multiple_choice"]


def _normalize(s: str) -> str:
    """Normalize answer for comparison."""
    return (s or "").strip().lower()


def _answers_match(user: str, correct: str) -> bool:
    """Check if user answer matches correct (with normalization)."""
    u = _normalize(user)
    c = _normalize(correct)
    if u == c:
        return True
    return False


async def get_next_question(
    db: AsyncSession, user_id: int, last_vocab_id: int | None = None
) -> dict | None:
    """
    Get next question for the game.
    Prioritizes lowest mastery, avoids immediate repeat.
    """
    q = (
        select(UserVocabulary, Vocabulary)
        .join(Vocabulary, UserVocabulary.vocabulary_id == Vocabulary.id)
        .where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.status == "in_progress",
        )
    )
    result = await db.execute(q)
    rows = list(result.all())
    if not rows:
        return None

    if last_vocab_id and len(rows) > 1:
        filtered = [r for r in rows if r[1].id != last_vocab_id]
        if filtered:
            rows = filtered
    rows = sorted(rows, key=lambda r: (getattr(r[0], "mastery", 0), r[0].last_reviewed_at or datetime.min))
    uv, v = rows[0]
    mode = random.choice(GAME_MODES)

    payload = {
        "mode": mode,
        "vocab_id": v.id,
        "user_vocab_id": uv.id,
        "prompt": "",
        "options": None,
        "expected_language": "ru",
    }

    if mode == "flashcard":
        payload["prompt"] = v.word_kz
        payload["expected_language"] = "ru"

    elif mode == "reverse":
        payload["prompt"] = v.translation_ru
        payload["expected_language"] = "kz"

    elif mode == "multiple_choice":
        payload["prompt"] = v.word_kz
        payload["expected_language"] = "ru"
        correct = v.translation_ru
        q_others = (
            select(Vocabulary.translation_ru)
            .where(Vocabulary.id != v.id)
            .limit(10)
        )
        others_result = await db.execute(q_others)
        others = list({row[0] for row in others_result.all() if row[0] != correct})
        random.shuffle(others)
        options = [correct] + others[:3]
        random.shuffle(options)
        payload["options"] = options[:4]

    return payload


async def submit_answer(
    db: AsyncSession, user_id: int, vocab_id: int, mode: str, user_answer: str
) -> dict:
    """
    Evaluate answer, update mastery, possibly set status to learned.
    """
    result = await db.execute(
        select(UserVocabulary, Vocabulary)
        .join(Vocabulary, UserVocabulary.vocabulary_id == Vocabulary.id)
        .where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.vocabulary_id == vocab_id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise ValueError("Word not found in your vocabulary")

    uv, v = row
    correct_answer = v.translation_ru if mode in ("flashcard", "multiple_choice") else v.word_kz
    is_correct = _answers_match(user_answer, correct_answer)

    if is_correct:
        uv.mastery = min(uv.mastery + 1, MASTERY_LEARNED)
    else:
        uv.mastery = max(uv.mastery - 1, 0)

    uv.last_reviewed_at = datetime.utcnow()
    if uv.mastery >= MASTERY_LEARNED:
        uv.status = "learned"

    await db.flush()
    await db.refresh(uv)

    return {
        "is_correct": is_correct,
        "mastery": uv.mastery,
        "status": uv.status,
        "correct_answer": correct_answer if not is_correct else None,
    }
