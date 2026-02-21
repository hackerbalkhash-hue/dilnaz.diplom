"""Vocabulary business logic."""
import re
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vocabulary import Vocabulary, UserVocabulary


async def lookup_word(db: AsyncSession, query: str) -> dict | None:
    """
    Search vocabulary by Kazakh word or Russian translation.
    Prefer exact match, then substring. Used by assistant for word explanations.
    """
    q = query.strip().lower()
    if not q or len(q) < 2:
        return None

    def to_row(v):
        return {
            "id": v.id,
            "word_kz": v.word_kz,
            "translation_ru": v.translation_ru,
            "transcription": v.transcription,
            "example_sentence": v.example_sentence,
        }

    # 1) Exact match first
    exact = await db.execute(
        select(Vocabulary).where(
            or_(
                Vocabulary.word_kz.ilike(q),
                Vocabulary.translation_ru.ilike(q),
            )
        )
    )
    v = exact.scalars().first()
    if v:
        return to_row(v)

    # 2) Substring match - prefer shortest (most specific) match for short queries
    sub = await db.execute(
        select(Vocabulary).where(
            or_(
                Vocabulary.word_kz.ilike(f"%{q}%"),
                Vocabulary.translation_ru.ilike(f"%{q}%"),
            )
        )
    )
    rows = list(sub.scalars().all())
    if not rows:
        return None
    # For query like "сәлем", prefer "сәлем" over "сәлемдесу"
    exact_len = [r for r in rows if r.word_kz.lower() == q or r.translation_ru.lower() == q]
    if exact_len:
        return to_row(exact_len[0])
    # Prefer word_kz that starts with or equals query
    for r in sorted(rows, key=lambda x: len(x.word_kz)):
        if r.word_kz.lower().startswith(q) or q in r.word_kz.lower():
            return to_row(r)
    return to_row(rows[0])


async def get_mentioned_words_in_text(
    db: AsyncSession, text: str, max_words: int = 10
) -> list[dict]:
    """
    Extract single Kazakh words from text that exist in Vocabulary.
    Returns list of {word_kz, vocabulary_id} for "Add to dictionary" buttons.
    """
    if not text or len(text) < 2:
        return []
    # Tokenize: letters (Cyrillic including Kazakh әғқңөұүһі)
    words = re.findall(r"[а-яёәғқңөұүһіa-z]+", text, re.I)
    seen = set()
    out = []
    for w in words:
        if len(w) < 2 or len(w) > 30 or w.lower() in seen:
            continue
        w_clean = w.strip()
        if not w_clean:
            continue
        result = await db.execute(
            select(Vocabulary).where(Vocabulary.word_kz.ilike(w_clean))
        )
        v = result.scalars().first()
        if v and v.word_kz.lower() == w_clean.lower():
            seen.add(w_clean.lower())
            out.append({"word_kz": v.word_kz, "vocabulary_id": v.id})
            if len(out) >= max_words:
                break
    return out


async def get_user_vocab_status(
    db: AsyncSession, user_id: int, vocabulary_id: int
) -> dict | None:
    """Get user's vocabulary status for a word (in_progress / learned, mastery)."""
    result = await db.execute(
        select(UserVocabulary).where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.vocabulary_id == vocabulary_id,
        )
    )
    uv = result.scalar_one_or_none()
    if not uv:
        return None
    return {
        "status": uv.status,
        "mastery": getattr(uv, "mastery", 0),
    }


async def add_word_to_user(
    db: AsyncSession,
    user_id: int,
    vocabulary_id: int | None = None,
    word_kz: str | None = None,
    translation_ru: str | None = None,
    transcription: str | None = None,
    example_sentence: str | None = None,
    source: str = "manual",
) -> UserVocabulary:
    """Add word to user vocabulary. Create Vocabulary if needed."""
    if vocabulary_id:
        existing = await db.execute(
            select(UserVocabulary).where(
                UserVocabulary.user_id == user_id,
                UserVocabulary.vocabulary_id == vocabulary_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Word already in vocabulary")
        uv = UserVocabulary(
            user_id=user_id,
            vocabulary_id=vocabulary_id,
            source=source,
        )
    else:
        if not word_kz or not translation_ru:
            raise ValueError("word_kz and translation_ru required")
        vocab = Vocabulary(
            word_kz=word_kz,
            translation_ru=translation_ru,
            transcription=transcription,
            example_sentence=example_sentence,
        )
        db.add(vocab)
        await db.flush()
        uv = UserVocabulary(
            user_id=user_id,
            vocabulary_id=vocab.id,
            source=source,
        )
    db.add(uv)
    await db.flush()
    await db.refresh(uv)
    return uv
