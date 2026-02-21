"""Assistant (chatbot) API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.schemas import ChatMessage, ChatResponse, MentionedWord
from app.assistant.service import process_message
from app.vocabulary.service import get_mentioned_words_in_text

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatMessage,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Send message to smart educational assistant.
    Context-aware, error-aware. Returns source + mentioned_words for UI.
    """
    context_dict = None
    if data.context:
        context_dict = {
            "lesson_id": data.context.lesson_id,
            "lesson_topic": data.context.lesson_topic,
            "mode": data.context.mode or "free",
            "user_level": data.context.user_level or "A1",
            "last_error_type": data.context.last_error_type,
            "refine_mode": data.context.refine_mode,
            "last_topic": data.context.last_topic,
            "last_rule": data.context.last_rule,
        }
    response_text, suggestions, source, last_topic, last_rule = await process_message(
        db,
        current_user.id,
        data.message,
        context_dict,
    )
    suggestions = suggestions or []
    mentioned = await get_mentioned_words_in_text(db, response_text)
    mentioned_words = [MentionedWord(word_kz=m["word_kz"], vocabulary_id=m["vocabulary_id"]) for m in mentioned]

    nav_buttons = []
    quick_replies = []
    for s in suggestions:
        s_lower = s.lower()
        if s in ("Уроки", "Словарь") or "добавить" in s_lower or "открыть урок" in s_lower or "перечитать" in s_lower or "подробнее" in s_lower:
            nav_buttons.append(s)
        else:
            quick_replies.append(s)
    return ChatResponse(
        response=response_text,
        suggestions=suggestions,
        nav_buttons=nav_buttons,
        quick_replies=quick_replies,
        source=source,
        mentioned_words=mentioned_words,
        last_topic=last_topic,
        last_rule=last_rule,
    )
