"""Assistant schemas."""
from pydantic import BaseModel


class MentionedWord(BaseModel):
    word_kz: str
    vocabulary_id: int


class AssistantContext(BaseModel):
    """Context for smart assistant. Mandatory for traceable responses."""
    lesson_id: int | None = None
    lesson_topic: str | None = None
    mode: str = "free"  # lesson | test | vocabulary | free
    user_level: str = "A1"
    last_error_type: str | None = None  # vocabulary | grammar | word_order | spelling
    refine_mode: str | None = None  # simple | detailed | examples — quick actions
    last_topic: str | None = None
    last_rule: str | None = None


class ChatMessage(BaseModel):
    message: str
    context: AssistantContext | None = None


class ChatResponse(BaseModel):
    response: str
    suggestions: list[str] = []
    nav_buttons: list[str] = []   # e.g. ["Уроки", "Словарь"]
    quick_replies: list[str] = []  # e.g. ["Что значит сәлем?", "Какой порядок слов..."]
    source: str = "grammar_rule"   # dictionary | lesson | grammar_rule
    mentioned_words: list[MentionedWord] = []  # for "Добавить в словарь" buttons
    last_topic: str | None = None
    last_rule: str | None = None
