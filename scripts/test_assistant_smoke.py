"""
Smoke test for assistant: grammar, lesson_explanation, sentence_check, refine, source.
Run: python -m scripts.test_assistant_smoke
Shows Q/A, intent, mode, source for commission demo.
"""
import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding for Kazakh characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # py3.7+

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant.service import (
    process_message,
    _detect_intent,
    _route_grammar_rule,
    parse_lesson_number,
    _extract_sentence_to_check,
)
from app.core.database import async_session_maker, init_db


async def run_smoke():
    await init_db()

    test_cases = [
        # --- Original: grammar & lesson ---
        ("Какие правила есть в казахском языке?", {"mode": "free"}),
        ("Какой порядок слов в казахском?", {"mode": "free"}),
        ("Объясни 2 урок", {"mode": "free"}),
        ("Объясни 10 урок", {"mode": "free"}),
        ("Что значит сәлем?", {"mode": "free"}),
        # --- New: sentence_check (5 cases) ---
        ("Проверь: Мен кітап оқыдым", {"mode": "free"}),
        ("Правильно ли написано: Ол жазады", {"mode": "free"}),
        ("Исправь предложение: Сен қалайсыз", {"mode": "free"}),
        ("Проверь Мен оқимын", {"mode": "free"}),
        ("тексер: Біз үйде отырмыз", {"mode": "free"}),
        ("дұрыс па: Кітап үлкен", {"mode": "free"}),
        ("Проверь предложение (без текста)", {"mode": "free"}),
        # --- New: refine_mode (3 cases) ---
        ("Проще", {"mode": "free", "refine_mode": "simple", "last_topic": "Порядок слов", "last_rule": "word_order"}),
        ("Подробнее", {"mode": "free", "refine_mode": "detailed", "last_rule": "sen_siz"}),
        ("Примеры", {"mode": "free", "refine_mode": "examples", "last_rule": "present_endings"}),
    ]

    print("=" * 80)
    print("ASSISTANT SMOKE TEST — Grammar, Lesson, Sentence check, Refine, Source")
    print("=" * 80)

    async with async_session_maker() as db:
        for i, (msg, ctx) in enumerate(test_cases, 1):
            intent = _detect_intent(msg)
            grammar_rule = _route_grammar_rule(msg) if intent == "grammar_question" else "-"
            mode = ctx.get("mode", "free")
            lesson_id = ctx.get("lesson_id", "")
            refine = ctx.get("refine_mode", "")

            result = await process_message(db, user_id=1, message=msg, context=ctx)
            response, suggestions, source, last_topic, last_rule = result

            print(f"\n--- Test {i} ---")
            print(f"Q: {msg}")
            print(f"Context: mode={mode}, lesson_id={lesson_id}, refine_mode={refine or '-'}")
            print(f"Intent: {intent} | Grammar rule: {grammar_rule} | Source: {source}")
            print(f"last_topic={last_topic!r} last_rule={last_rule!r}")
            print(f"A: {response[:400]}{'...' if len(response) > 400 else ''}")
            if suggestions:
                print(f"Suggestions: {suggestions[:5]}")
            print()

    # Extra: _extract_sentence_to_check
    print("--- _extract_sentence_to_check ---")
    for phrase in ["Проверь: Мен оқимын", "Исправь «Ол жазады»", "правильно ли Ол келді"]:
        sent = _extract_sentence_to_check(phrase)
        print(f"  {phrase!r} -> {sent!r}")

    print("=" * 80)
    print("Smoke test completed.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_smoke())
