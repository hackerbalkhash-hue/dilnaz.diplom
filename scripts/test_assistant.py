"""
QA Test Script: Virtual Assistant Black-Box Testing.
Does NOT modify assistant logic. Only tests and reports.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant.service import process_message
from app.core.database import async_session_maker, init_db

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "assistant_test_results.txt"


async def run_test(message: str, context: dict, db) -> tuple[str, list]:
    """Call assistant and return (response, suggestions)."""
    try:
        response, suggestions = await process_message(db, user_id=1, message=message, context=context)
        return response or "(empty)", suggestions or []
    except Exception as e:
        return f"[ERROR: {e}]", []


def log(f, s=""):
    f.write(str(s) + "\n")
    f.flush()


async def main():
    await init_db()
    test_cases = [
        # A) Vocabulary
        ("Что значит слово «сәлем»?", {"mode": "free"}),
        ("Как переводится «рахмет»?", {"mode": "free"}),
        ("Что означает «ана»?", {"mode": "free"}),
        ("Перевод слова жақсы", {"mode": "free"}),
        ("Что значит сәлем?", {"mode": "vocabulary"}),
        ("Что значит сәлем?", {"mode": "test"}),
        # B) Grammar
        ("Почему используется «мен»?", {"mode": "free"}),
        ("Как сказать «я студент» по-казахски?", {"mode": "free"}),
        ("В чём разница между «сәлем» и «сәлеметсіз бе»?", {"mode": "free"}),
        ("Объясни правило про окончания", {"mode": "free"}),
        ("Какой порядок слов в казахском?", {"mode": "free"}),
        # C) Lesson context
        ("Объясни урок про приветствия", {"mode": "lesson", "lesson_id": 2}),
        ("Что я должен понять в этом уроке?", {"mode": "lesson", "lesson_id": 2}),
        ("Что значит сәлем?", {"mode": "lesson", "lesson_id": 2}),
        # D) Error explanation
        ("Почему это неправильно?", {"mode": "free"}),
        ("В чём моя ошибка?", {"mode": "free"}),
        ("Подскажи, не понимаю", {"mode": "test"}),
        ("Подскажи, не понимаю", {"mode": "lesson", "lesson_id": 2, "last_error_type": "grammar"}),
        # E) Out-of-scope
        ("Какая погода завтра?", {"mode": "free"}),
        ("Сколько лет президенту Казахстана?", {"mode": "free"}),
        # General
        ("Привет", {"mode": "free"}),
        ("Помощь", {"mode": "free"}),
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        log(f, "=" * 80)
        log(f, "VIRTUAL ASSISTANT QA TEST REPORT")
        log(f, "=" * 80)

        async with async_session_maker() as db:
            for i, (msg, ctx) in enumerate(test_cases, 1):
                resp, sugg = await run_test(msg, ctx, db)
                mode = ctx.get("mode", "free")
                lesson_id = ctx.get("lesson_id", "")
                log(f, f"\n--- Test {i} ---")
                log(f, f"Question: {msg}")
                log(f, f"Context: mode={mode}, lesson_id={lesson_id}")
                log(f, f"Response: {resp[:600]}{'...' if len(resp) > 600 else ''}")
                if sugg:
                    log(f, f"Suggestions: {sugg}")
                log(f)

        log(f, "=" * 80)
        log(f, "Tests completed.")
        log(f, "=" * 80)

    print(f"Report written to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
