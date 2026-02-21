"""
Rule-based educational assistant. CLEAR, EXPLAINABLE, CONTEXT-AWARE.
Uses ONLY platform data: lesson content, vocabulary DB, A1 grammar rules.
Every answer is traceable to its source.
"""
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.rules import (
    INTENT_PATTERNS,
    GRAMMAR_KB,
    A1_GRAMMAR_RULES,
    TEST_MODE_RESPONSE,
    FALLBACK,
)
from app.lessons.service import get_lesson_for_assistant, get_lesson_by_order_index
from app.vocabulary.service import lookup_word, get_user_vocab_status, get_mentioned_words_in_text

logger = logging.getLogger(__name__)

# Intent priority: first in list = highest priority
INTENT_PRIORITY = [
    "lesson_explanation",
    "lesson_errors",
    "sentence_check",
    "error_explanation",
    "vocabulary_question",
    "grammar_question",
    "general_help",
]

FALLBACK_SUGGESTIONS = [
    "Объясни этот урок",
    "Какие ошибки в этом уроке?",
    "Объясни грамматику",
    "Что значит сәлем?",
    "Какой порядок слов в казахском?",
]

# Result: (text, suggestions, source, last_topic, last_rule). source = "dictionary" | "lesson" | "grammar_rule"
def _r(text: str, suggestions: list[str], source: str = "grammar_rule", last_topic: str | None = None, last_rule: str | None = None):
    return (text, suggestions or [], source, last_topic, last_rule)


def _detect_intent(message: str) -> str:
    """Classify message into exactly one intent. Priority order applied."""
    msg_lower = (message or "").lower().strip()
    if not msg_lower:
        return "unknown"

    # "Объясни 5 урок", "Объясни 10 урок" и т.д. — lesson_explanation по номеру
    if parse_lesson_number(message or "") and any(
        w in msg_lower for w in ("объясни", "урок", "разбор", "о чем", "что в уроке")
    ):
        return "lesson_explanation"

    for intent in INTENT_PRIORITY:
        keywords = INTENT_PATTERNS.get(intent, [])
        for kw in keywords:
            if kw in msg_lower:
                return intent

    return "unknown"


def _get_context_mode(context: dict | None) -> str:
    """Validate mode: lesson | test | vocabulary | free."""
    if not context:
        return "free"
    mode = (context.get("mode") or "free").lower()
    if mode in ("lesson", "test", "vocabulary", "free"):
        return mode
    return "free"


def parse_lesson_number(message: str) -> int | None:
    """
    Extract 1-based lesson number from message.
    Supports: "объясни 2 урок", "урок 5", "разбор урока 10", "объясни урок №3".
    Returns number or None.
    """
    msg = message.strip()
    patterns = [
        r"объясни\s+(\d+)\s*(?:й|ый|ий)?\s*урок",
        r"объясни\s+урок\s+[№#]?\s*(\d+)",
        r"разбор\s+урока\s+(\d+)",
        r"урок\s+(\d+)",
        r"(\d+)\s*урок",
        r"[№#]\s*(\d+)\s*урок",
    ]
    for pat in patterns:
        m = re.search(pat, msg, re.I)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 100:
                return n
    return None


# Spelling variants: common user typos -> correct Kazakh form
SPELLING_VARIANTS: dict[str, str] = {
    "рахмет": "рақмет",
    "салем": "сәлем",
    "салам": "сәлем",
    "жаксы": "жақсы",
    "кешириниз": "кешіріңіз",
    "отынемин": "өтінемін",
}


def _normalize_word(word: str) -> str:
    """Normalize spelling variants (рахмет -> рақмет, etc.)."""
    w = word.strip().lower()
    return SPELLING_VARIANTS.get(w, w)


def _clean_word(word: str) -> str:
    """Remove punctuation and extra whitespace from extracted word."""
    return re.sub(r"[«»\"'?.,;:!]+", "", word).strip()


def _extract_word_from_message(message: str) -> str | None:
    """
    Extract word from message. Priority:
    1) Word in guillemets «...» or quotes "..."
    2) Word after "слово", "что значит", etc.
    3) Last token if message is short (fallback)
    """
    msg = message.strip()
    # 1) Priority: word in «...» or "..."
    quoted = re.findall(r"[«\"]([^»\"]+)[»\"]", msg)
    if quoted:
        for q in quoted:
            cleaned = _clean_word(q)
            if len(cleaned) >= 2 and cleaned.lower() not in ("что", "как", "слово", "это"):
                return _normalize_word(cleaned)
    # Стоп-слова: не считать искомым словом при "как будет X"
    _skip = ("что", "как", "слово", "это", "этот", "на", "по", "в", "казахском", "казахски", "языке")
    # 2) Patterns: "слово X", "что значит X", "перевод слова X", "как будет на казахском X"
    patterns = [
        r"слово\s+([а-яёәғқңөұүһі\w\-]+)",
        r"(?:что значит|как переводится|значение слова|что такое)\s*[:\"]?\s*([а-яёәғқңөұүһі\w\-]+)",
        r"(?:как будет|как сказать)\s+на казахском\s+([а-яёәғқңөұүһі\w\-]+)",
        r"(?:как будет|по-казахски)\s+([а-яёәғқңөұүһі\w\-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, msg, re.I)
        if m:
            cleaned = _clean_word(m.group(1))
            if len(cleaned) >= 2 and cleaned.lower() not in _skip:
                return _normalize_word(cleaned)
    # 3) Fallback: last token if short message
    if len(msg.split()) <= 4:
        parts = msg.split()
        for p in reversed(parts):
            cleaned = _clean_word(p)
            if len(cleaned) >= 2 and cleaned.lower() not in ("что", "как", "слово", "это", "этот"):
                return _normalize_word(cleaned)
    return None


def _route_grammar_rule(message: str) -> str:
    """Map message to grammar rule id from GRAMMAR_KB. Returns rule key or 'default'."""
    msg = message.lower()
    # word_order
    if any(x in msg for x in ["порядок", "слов", "подлежащ", "сөз тәртіб", "дополнени", "глагол"]):
        return "word_order"
    # sen_siz / formal_informal
    if any(x in msg for x in ["сіз", "сен", "привет", "формаль", " мен", "мен?", "мен.", "разница сен", "разница сіз", "в чем разница", "в чём разница", "айырмашылық"]):
        return "sen_siz"
    # present_endings
    if any(x in msg for x in ["настоящ", "врем", "спряж", "окончани", "-мын", "-сың"]):
        return "present_endings"
    # plural
    if any(x in msg for x in ["множествен", "множеств", "plural", "-лар", "-лер"]):
        return "plural"
    # question_particles
    if any(x in msg for x in ["вопрос", "частица", "ма ", "ме ", "қалай"]):
        return "question_particles"
    # cases_intro
    if any(x in msg for x in ["падеж", "септік", "дательн", "местн", "винительн"]):
        return "cases_intro"
    # negation_intro
    if any(x in msg for x in ["отрицан", "емес", "жоқ"]):
        return "negation_intro"
    # affixes
    if any(x in msg for x in ["окончани", "аффикс", "суффикс", "корень", "жалғау", "жұрнақ"]):
        return "affixes"
    return "default"


def _extract_learning_objective(content: str, max_chars: int = 500) -> str | None:
    """Extract Оқу мақсаты / Цель урока from lesson content."""
    if not content or ("Оқу мақсаты" not in content and "Цель урока" not in content):
        return None
    for marker in ("Оқу мақсаты", "Цель урока"):
        idx = content.find(marker)
        if idx >= 0:
            end = content.find("\n## ", idx + 1)
            if end < 0:
                end = len(content)
            block = content[idx:end].replace(marker, "").strip()
            block = re.sub(r"\([^)]*\)", "", block).strip()
            if block:
                return block[:max_chars] + ("..." if len(block) > max_chars else "")
    return None


def _extract_grammar_focus(content: str, max_chars: int = 400) -> str | None:
    """Extract Грамматикалық нүкте / grammar section from lesson content."""
    if not content:
        return None
    for marker in ("Грамматикалық нүкте", "грамматик"):
        idx = content.lower().find(marker.lower())
        if idx >= 0:
            end = content.find("\n## ", idx + 1)
            if end < 0:
                end = len(content)
            block = content[idx:end].strip()
            if len(block) >= 20:
                return block[:max_chars] + ("..." if len(block) > max_chars else "")
    return None


def _extract_mistakes_section(content: str, max_chars: int = 400) -> str | None:
    """Extract Жиі қателер / Частые ошибки from lesson content."""
    if not content or "Жиі қателер" not in content:
        return None
    idx = content.find("Жиі қателер")
    end = content.find("\n## ", idx + 1)
    if end < 0:
        end = min(idx + max_chars, len(content))
    return content[idx:end].strip()[:max_chars]


def _extract_examples_section(content: str, max_chars: int = 300) -> str | None:
    """Extract Мысалдар / Примеры from lesson content."""
    if not content:
        return None
    for marker in ("Мысалдар", "Примеры", "section3_examples"):
        idx = content.find(marker)
        if idx >= 0:
            end = content.find("\n## ", idx + 1)
            if end < 0:
                end = len(content)
            block = content[idx:end].strip()
            if len(block) >= 20:
                return block[:max_chars]
    return None


async def _get_lesson_data(db: AsyncSession, lesson_id: int | None) -> dict | None:
    """Fetch lesson from platform."""
    if not lesson_id:
        return None
    return await get_lesson_for_assistant(db, lesson_id)


EMPTY_BLOCK_MSG = "Бұл бөлім толтырылмаған."


def _extract_sentence_to_check(message: str) -> str | None:
    """Extract sentence to check (1–12 words). From quotes or after trigger words."""
    msg = (message or "").strip()
    # In «...» or "..." or '...'
    for pattern in [r"[«\"']([^»\"']{2,120})[»\"']", r"«([^»]+)»"]:
        m = re.search(pattern, msg)
        if m:
            s = m.group(1).strip()
            words = len(s.split())
            if 1 <= words <= 12:
                return s
    # After "проверь", "исправь", "правильно ли" etc. — take rest of message or next phrase
    for trigger in ["проверь", "исправь", "правильно ли", "тексер", "дұрыс па", "проверь предложение"]:
        idx = msg.lower().find(trigger)
        if idx >= 0:
            rest = msg[idx + len(trigger):].strip()
            rest = re.sub(r"^[:—\-]+", "", rest).strip()
            if rest:
                words = rest.split()[:12]
                if words:
                    return " ".join(words) if len(words) <= 12 else " ".join(words[:12])
    # Whole message if short enough
    words = msg.split()
    if 1 <= len(words) <= 12 and any(c in msg for c in "әғқңөұүһі"):
        return msg
    return None


def _build_sentence_check_response(sentence: str) -> tuple[str, list[str]]:
    """
    Rule-based check: SOV, сен/сіз, present endings, plural, question particles.
    Returns: Қате табылды:, Неге?, Дұрыс нұсқа:, Қосымша мысал:
    """
    s = sentence.strip()
    words = s.split()
    errors = []
    reasons = []
    corrects = []
    # Present endings
    present_endings = ("мын", "мін", "сың", "сің", "сыз", "сіз", "ды", "ді", "ты", "ті")
    has_verb_ending = any(w.endswith(present_endings) for w in words for p in present_endings if len(w) > 2)
    # SOV: verb often at end (last or second-to-last word)
    last = words[-1] if words else ""
    verb_at_end = any(last.endswith(e) for e in present_endings) or last.endswith("ды") or last.endswith("ді")
    if words and not verb_at_end and len(words) >= 2:
        # Maybe verb in wrong place
        if not has_verb_ending:
            errors.append("Етістік сөйлем соңында болуы керек (SOV).")
            reasons.append("Қазақ тілінде тәртіп: подлежащее + толықтауыш + етістік.")
            corrects.append("Мысалы: Мен кітап оқыдым. (Подлежащее + дополнение + глагол.)")
    # сен/сіз: mixing -ңыз with сен
    if "сен" in s.lower() and ("ңыз" in s or "ыңыз" in s):
        errors.append("«Сен» бейресми; «-ңыз» формальды жұрнақ — сәйкессіздік.")
        reasons.append("Үлкендерге «сіз» және «-ңыз»/«-ыңыз» қолданыңыз.")
        corrects.append("Сіз қалайсыз? (формальды)")
    # Question: ма/ме/ба/бе
    if "?" in s or s.endswith("ма") or s.endswith("ме") or s.endswith("ба") or s.endswith("бе"):
        if not any(s.rstrip("?").strip().endswith(p) for p in ("ма", "ме", "ба", "бе")):
            pass  # question by intonation, OK
    if not errors:
        text = (
            "**Қате табылды:** жоқ.\n\n"
            "**Неге?** Сөйлем грамматикалық түрде дұрыс болып көрінеді (SOV, жұрнақтар).\n\n"
            "**Дұрыс нұсқа:** өзгерту қажет емес.\n\n"
            "**Қосымша мысал:** Мен оқимын. (Я читаю.)"
        )
    else:
        err_block = "\n".join(f"• {e}" for e in errors)
        rea_block = "\n".join(f"• {r}" for r in reasons)
        cor_block = "\n".join(f"• {c}" for c in corrects)
        example = GRAMMAR_KB["word_order"]["examples"][0] if GRAMMAR_KB else "Мен кітап оқыдым."
        text = (
            f"**Қате табылды:**\n{err_block}\n\n"
            f"**Неге?**\n{rea_block}\n\n"
            f"**Дұрыс нұсқа:**\n{cor_block}\n\n"
            f"**Қосымша мысал:** {example}"
        )
    suggestions = ["Проверь другое предложение", "Какой порядок слов в казахском?", "Объясни 2 урок"]
    return text, suggestions


async def _build_lesson_explanation(
    db: AsyncSession,
    lesson: dict,
) -> tuple[str, list[str]]:
    """
    Generate structured lesson explanation: Topic, Goal, Main rule, Examples, Common errors.
    Empty blocks -> "Бұл бөлім толтырылмаған."
    """
    content = lesson.get("content") or ""
    title = lesson.get("title", "Урок")
    topic = lesson.get("topic", "")

    parts = []
    parts.append(f"**Тақырыбы / Тема:** {topic or EMPTY_BLOCK_MSG}")

    obj = _extract_learning_objective(content)
    parts.append(f"\n**Мақсаты / Цель:**\n{obj if obj else EMPTY_BLOCK_MSG}")

    grammar = _extract_grammar_focus(content, max_chars=350)
    parts.append(f"\n**Негізгі ереже / Основное правило:**\n{grammar if grammar else EMPTY_BLOCK_MSG}")

    examples = _extract_examples_section(content)
    parts.append(f"\n**Мысалдар / Примеры:**\n{examples if examples else EMPTY_BLOCK_MSG}")

    mistakes = _extract_mistakes_section(content)
    parts.append(f"\n**Жиі қателер / Частые ошибки:**\n{mistakes if mistakes else EMPTY_BLOCK_MSG}")

    text = "".join(parts)
    suggestions = ["Объясни этот урок", "Какие ошибки в этом уроке?", "Объясни грамматику"]
    return text, suggestions


async def _build_vocabulary_response(
    db: AsyncSession,
    user_id: int,
    word_query: str,
    context_mode: str,
    lesson: dict | None,
) -> tuple[str, list[str]]:
    """Use ONLY vocabulary from platform DB. In test mode: no translations."""
    if context_mode == "test":
        return TEST_MODE_RESPONSE, []

    vocab = await lookup_word(db, word_query)
    if not vocab:
        return (
            f"Слово «{word_query}» не найдено в словаре платформы. "
            "Проверьте написание или добавьте слово в разделе «Словарь».",
            ["Добавить слово в словарь"],
        )

    source = "Из словаря платформы"
    parts = [f"{source}: «{vocab['word_kz']}» — {vocab['translation_ru']}."]

    if vocab.get("example_sentence"):
        parts.append(f"Пример: {vocab['example_sentence']}.")

    user_status = await get_user_vocab_status(db, user_id, vocab["id"])
    suggestion = []
    if user_status:
        status = "изучаете" if user_status["status"] == "in_progress" else "изучено"
        parts.append(f"В вашем словаре: {status} (мастерство {user_status['mastery']}/5).")
    else:
        parts.append("Можете добавить в личный словарь в разделе «Словарь».")
        suggestion = ["Добавить в словарь"]

    if lesson:
        parts.insert(1, f"Урок «{lesson['title']}» также содержит это слово.")

    return " ".join(parts), suggestion


def _build_general_grammar_summary() -> str:
    """Structured A1 grammar overview for 'какие правила' / 'грамматика' / 'основные правила'."""
    rules = [
        ("1. Порядок слов (SOV)", GRAMMAR_KB["word_order"]["explanation"], GRAMMAR_KB["word_order"]["examples"][0]),
        ("2. Сен/Сіз (формальность)", GRAMMAR_KB["sen_siz"]["explanation"], GRAMMAR_KB["sen_siz"]["examples"][0]),
        ("3. Окончания настоящего времени", GRAMMAR_KB["present_endings"]["explanation"], GRAMMAR_KB["present_endings"]["examples"][0]),
        ("4. Вопросы (ма/ме/ба/бе)", GRAMMAR_KB["question_particles"]["explanation"], GRAMMAR_KB["question_particles"]["examples"][0]),
        ("5. Множественное число (-лар/-лер)", GRAMMAR_KB["plural"]["explanation"], GRAMMAR_KB["plural"]["examples"][0]),
        ("6. Падежи (септік)", GRAMMAR_KB["cases_intro"]["explanation"], GRAMMAR_KB["cases_intro"]["examples"][0]),
    ]
    parts = ["**Основные правила грамматики A1 (казахский язык):**\n"]
    for title, expl, ex in rules:
        parts.append(f"\n**{title}**\n{expl}\nПример: {ex}")
    return "\n".join(parts)


async def _build_grammar_response(
    db: AsyncSession,
    message: str,
    context_mode: str,
    lesson: dict | None,
) -> tuple[str, list[str]]:
    """
    Use GRAMMAR_KB. In test mode: allow grammar explanation, no vocabulary/answers.
    """
    msg_lower = message.lower()
    lesson_content = (lesson or {}).get("content") or ""

    # При наличии урока — сначала грамматика этого урока, потом общие правила
    lesson_block = ""
    if lesson_content and lesson:
        grammar = _extract_grammar_focus(lesson_content, max_chars=400)
        if grammar:
            lesson_block = f"**Из урока «{lesson['title']}»:**\n{grammar}\n\n"

    # Обзор «какие правила» / «объясни грамматику» — НЕ отказываем, всегда даём структурированный ответ
    if any(p in msg_lower for p in ["какие правила", "правила есть", "основные правила", "правила в казахском", "объясни грамматику"]) or (
        "грамматик" in msg_lower and any(x in msg_lower for x in ["какие", "основн", "что есть", "расскажи", "объясни"])
    ):
        text = lesson_block + _build_general_grammar_summary()
        suggestions = ["Объясни этот урок", "Какие ошибки в этом уроке?", "Какой порядок слов в казахском?", "В чем разница сен и сіз?"]
        if lesson:
            suggestions = [f"Объясни урок «{lesson['title']}»", "Какие ошибки в этом уроке?"] + suggestions[:2]
        return text, suggestions

    # Конкретный вопрос по правилу — если есть урок, сначала из урока
    if lesson_block:
        rule_key = _route_grammar_rule(message)
        rule = GRAMMAR_KB.get(rule_key) or A1_GRAMMAR_RULES.get(rule_key)
        if rule:
            exs = rule.get("examples", [rule.get("example", "")])
            ex_str = "\n".join(f"• {e}" for e in (exs[:3] if isinstance(exs, list) else [exs]))
            from_lesson = lesson_block.strip() + "\n\n**Дополнительно (A1):** " + rule.get("explanation", "")
            if ex_str:
                from_lesson += "\n\nПримеры:\n" + ex_str
            return from_lesson, [f"Объясни урок «{lesson['title']}»", "Какие ошибки в этом уроке?"]

    # Только урок (грамматика урока)
    if lesson_content and lesson:
        grammar = _extract_grammar_focus(lesson_content)
        if grammar:
            text = f"**Из урока «{lesson['title']}»:**\n{grammar}"
            return text, [f"Объясни этот урок", "Какие ошибки в этом уроке?"]

    rule_key = _route_grammar_rule(message)
    rule = GRAMMAR_KB.get(rule_key) or A1_GRAMMAR_RULES.get(rule_key)
    if not rule:
        rule = A1_GRAMMAR_RULES.get("default", {"explanation": "Посмотрите раздел «Грамматика» в уроке.", "example": ""})

    if "examples" in rule:
        exs = rule["examples"][:3]
        examples_str = "\n".join(f"• {e}" for e in exs)
    else:
        examples_str = rule.get("example", "")

    source = "Правило грамматики (A1)"
    parts = [f"{source}: {rule['explanation']}"]
    if examples_str:
        parts.append(f"\nПримеры:\n{examples_str}")

    suggestion = ["Объясни этот урок", "Какие ошибки в этом уроке?"] if lesson else ["Объясни 1 урок", "Объясни грамматику", "Какой порядок слов в казахском?"]
    return "\n".join(parts), suggestion


async def _build_error_response(
    context: dict | None,
    context_mode: str,
    lesson: dict | None,
) -> tuple[str, list[str]]:
    """After wrong answer. NEVER give correct answer."""
    if context_mode == "test":
        return TEST_MODE_RESPONSE, []

    error_type = (context.get("last_error_type") or "default").lower()
    rule_key = "word_order" if "word_order" in error_type else "affixes" if "grammar" in error_type else "default"
    rule = GRAMMAR_KB.get(rule_key) or A1_GRAMMAR_RULES.get(rule_key, A1_GRAMMAR_RULES["default"])

    if lesson and lesson.get("content") and "Жиі қателер" in lesson["content"]:
        mistakes = _extract_mistakes_section(lesson["content"])
        if mistakes:
            source = f"Из урока «{lesson['title']}» (раздел «Частые ошибки»)"
            return f"{source}:\n{mistakes}", ["Объясни этот урок", "Какие ошибки в этом уроке?"]

    expl = rule.get("explanation", rule.get("example", ""))
    return f"Подсказка (правило): {expl}", ["Объясни этот урок", "Какие ошибки в этом уроке?"] if lesson else ["Объясни 1 урок", "Объясни грамматику"]


async def _build_general_help_response(
    context_mode: str,
    lesson: dict | None,
) -> tuple[str, list[str]]:
    """General help: конкретные кнопки-вопросы, без шаблона «задайте вопрос»."""
    if lesson:
        return (
            f"Я помощник по казахскому языку. Сейчас вы в уроке «{lesson['title']}». "
            "Могу объяснить урок, грамматику или частые ошибки — нажмите кнопку ниже.",
            ["Объясни этот урок", "Какие ошибки в этом уроке?", "Объясни грамматику", "Что значит сәлем?"],
        )
    return (
        "Я помогаю с казахским языком. Могу объяснить урок, грамматику, частые ошибки или перевести слово. Выберите вопрос ниже.",
        ["Объясни 1 урок", "Объясни грамматику", "Какие ошибки в этом уроке?", "Что значит сәлем?", "Какой порядок слов в казахском?"],
    )


async def process_message(
    db: AsyncSession,
    user_id: int,
    message: str,
    context: dict | None,
) -> tuple[str, list[str], str, str | None, str | None]:
    """
    Main entry. Returns (text, suggestions, source, last_topic, last_rule).
    source = "dictionary" | "lesson" | "grammar_rule". Logs intent + source.
    """
    msg = (message or "").strip()
    if not msg:
        return _r(FALLBACK, FALLBACK_SUGGESTIONS, "grammar_rule")

    # Refine: Проще / Подробнее / Примеры
    refine_mode = (context or {}).get("refine_mode")
    last_topic = (context or {}).get("last_topic")
    last_rule = (context or {}).get("last_rule")
    if refine_mode and (last_topic or last_rule):
        rule = GRAMMAR_KB.get(last_rule or "default") or A1_GRAMMAR_RULES.get("default", {})
        expl = rule.get("explanation", "")
        exs = rule.get("examples", [rule.get("example", "")])
        if refine_mode == "simple":
            text = (expl[:300] + "..." if len(expl) > 300 else expl) if expl else "Кратко: см. правило выше."
        elif refine_mode == "detailed":
            text = expl + "\n\nПодробнее в уроке по грамматике."
            if exs:
                text += "\n\nПримеры:\n" + "\n".join(f"• {e}" for e in (exs[:3] if isinstance(exs, list) else [exs]))
        else:  # examples
            text = "**Примеры:**\n" + "\n".join(f"• {e}" for e in (exs[:5] if isinstance(exs, list) else [exs]))
        logger.info("assistant: intent=refine refine_mode=%s source=grammar_rule", refine_mode)
        return _r(text, ["Уроки", "Какой порядок слов в казахском?"], "grammar_rule", last_topic, last_rule)

    intent = _detect_intent(msg)
    context_mode = _get_context_mode(context)
    lesson_id = (context or {}).get("lesson_id")
    logger.info("assistant request: intent=%s mode=%s lesson_id=%s", intent, context_mode, lesson_id)
    user_level = (context or {}).get("user_level") or "A1"

    # Resolve lesson: ALWAYS from context when lesson_id present; else by number for lesson/grammar intents
    lesson = await _get_lesson_data(db, lesson_id) if lesson_id else None
    if not lesson and intent in ("lesson_explanation", "grammar_question", "lesson_errors"):
        lesson_num = parse_lesson_number(msg)
        if lesson_num:
            lesson = await get_lesson_by_order_index(db, lesson_num)

    source_knowledge = "grammar_rule"

    # lesson_explanation (highest priority) — всегда используем данные урока при lesson_id
    if intent == "lesson_explanation":
        used_source = "context.lesson_id" if lesson else None
        resolved_lesson_id = (lesson or {}).get("id")
        if not lesson:
            lesson_num = parse_lesson_number(msg)
            if lesson_num:
                lesson = await get_lesson_by_order_index(db, lesson_num)
                used_source = f"order_index({lesson_num})" if lesson else f"order_index({lesson_num}, not_found)"
                resolved_lesson_id = (lesson or {}).get("id")
            else:
                used_source = "parse_failed"
        logger.info(
            "LESSON_EXPLANATION: used_source=%s lesson_id=%s lesson_found=%s",
            used_source, resolved_lesson_id, lesson is not None,
        )
        if lesson:
            text, suggestions = await _build_lesson_explanation(db, lesson)
            source_knowledge = "lesson"
            logger.info("assistant: intent=%s source=%s", intent, source_knowledge)
            return _r(text, suggestions, source_knowledge, lesson.get("topic"), None)
        return _r(
            "Такого урока нет. Откройте раздел «Уроки» и выберите урок.",
            ["Объясни 1 урок", "Объясни 2 урок", "Какие правила есть в казахском?"],
            "grammar_rule",
        )

    # lesson_errors — частые ошибки урока (Жиі қателер)
    if intent == "lesson_errors":
        if lesson and lesson.get("content"):
            mistakes = _extract_mistakes_section(lesson["content"], max_chars=600)
            if mistakes:
                title = lesson.get("title", "Урок")
                text = f"**Жиі қателер / Частые ошибки** (урок «{title}»):\n\n{mistakes}"
                suggestions = ["Объясни этот урок", "Какие правила в этом уроке?", "Объясни грамматику"]
                logger.info("assistant: intent=lesson_errors source=lesson")
                return _r(text, suggestions, "lesson", lesson.get("topic"), None)
            text = f"В уроке «{lesson.get('title', 'Урок')}» раздел «Частые ошибки» пока не заполнен."
            return _r(text, ["Объясни этот урок", "Объясни грамматику"], "lesson", lesson.get("topic"), None)
        return _r(
            "Откройте урок (страница урока или чат с выбранным уроком), чтобы увидеть частые ошибки этого урока.",
            ["Объясни 1 урок", "Какие ошибки в этом уроке?"],
            "grammar_rule",
        )

    # sentence_check
    if intent == "sentence_check":
        sentence = _extract_sentence_to_check(msg)
        if sentence:
            text, suggestions = _build_sentence_check_response(sentence)
            logger.info("assistant: intent=sentence_check source=grammar_rule")
            return _r(text, suggestions, "grammar_rule", "Проверка предложения", "sentence_check")
        return _r(
            "Напишите предложение для проверки (1–12 слов). Например: «Проверь: Мен кітап оқыдым» или «Исправь: Ол жазады».",
            ["Проверь: Мен оқимын", "Какой порядок слов в казахском?"],
            "grammar_rule",
        )

    # error_explanation
    if intent == "error_explanation":
        text, suggestions = await _build_error_response(context, context_mode, lesson)
        source_knowledge = "lesson" if lesson else "grammar_rule"
        logger.info("assistant: intent=%s source=%s", intent, source_knowledge)
        return _r(text, suggestions, source_knowledge)


    # vocabulary_question — in test mode: no translations
    GRAMMAR_TERMS = {"падеж", "окончание", "спряжение", "склонение", "аффикс", "суффикс", "формально", "формаль"}
    if intent == "vocabulary_question":
        word = _extract_word_from_message(msg)
        if word and word.lower() in GRAMMAR_TERMS:
            text, suggestions = await _build_grammar_response(db, msg, context_mode, lesson)
            rule_key = _route_grammar_rule(msg)
            logger.info("assistant: intent=vocabulary_question->grammar source=dictionary")
            return _r(text, suggestions, "grammar_rule", None, rule_key)
        if word:
            if " " in word or len(word.split()) > 1:
                return _r(
                    "Я показываю перевод отдельных слов. Спросите о конкретном слове: «Что значит студент?»",
                    [],
                    "grammar_rule",
                )
            text, suggestions = await _build_vocabulary_response(db, user_id, word, context_mode, lesson)
            logger.info("assistant: intent=%s source=dictionary word=%s", intent, word)
            return _r(text, suggestions, "dictionary")
        return _r(
            "Укажите слово. Например: «Что значит сәлем?» или «Перевод слова рақмет».",
            ["Что значит сәлем?", "Перевод слова жақсы"],
            "grammar_rule",
        )

    # grammar_question — in test mode: allow grammar
    if intent == "grammar_question":
        text, suggestions = await _build_grammar_response(db, msg, context_mode, lesson)
        source_knowledge = "lesson" if lesson and "Из урока" in text else "grammar_rule"
        rule_key = _route_grammar_rule(msg)
        logger.info("assistant: intent=%s source=%s last_rule=%s", intent, source_knowledge, rule_key)
        return _r(text, suggestions, source_knowledge, None, rule_key)

    # general_help
    if intent == "general_help":
        text, suggestions = await _build_general_help_response(context_mode, lesson)
        logger.info("assistant: intent=%s source=grammar_rule", intent)
        return _r(text, suggestions, "grammar_rule")

    # unknown — improved fallback
    logger.info("assistant: intent=unknown source=grammar_rule")
    return _r(FALLBACK, FALLBACK_SUGGESTIONS, "grammar_rule")
