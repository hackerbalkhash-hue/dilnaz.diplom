"""
Seed educational content: ~3000 vocabulary, 60 lessons, 600+ exercises, 60 tests.
Idempotent - safe to run multiple times.
Run: python -m scripts.seed_content
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func

from app.core.database import async_session_maker, init_db
from app.models.lesson import Lesson, LessonPrerequisite
from app.models.exercise import Exercise
from app.models.test import Test, TestQuestion
from app.models.vocabulary import Vocabulary

from app.data.vocabulary_data import get_vocabulary
from app.data.lessons_data import get_lessons


def _build_full_vocabulary() -> list[dict]:
    """Build ~3000 vocabulary items from data + programmatic expansion."""
    base = get_vocabulary()
    seen = {v["word_kz"].strip().lower() for v in base}
    out = list(base)

    # Load from CSV if exists
    csv_path = Path(__file__).resolve().parent.parent / "data" / "vocabulary.csv"
    if csv_path.exists():
        import csv
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                kz = (row.get("word_kz") or "").strip()
                ru = (row.get("translation_ru") or "").strip()
                if kz and ru and kz.lower() not in seen:
                    seen.add(kz.lower())
                    out.append({"word_kz": kz, "translation_ru": ru, "transcription": None, "example_sentence": None})

    # Load from JSON files if exist
    import json
    for name in ("vocabulary.json", "vocabulary_bulk.json", "vocabulary_extended.json"):
        json_path = Path(__file__).resolve().parent.parent / "data" / name
        if json_path.exists():
            with open(json_path, encoding="utf-8") as f:
                for v in json.load(f):
                    kz = (v.get("word_kz") or "").strip()
                    ru = (v.get("translation_ru") or "").strip()
                    if kz and ru and kz.lower() not in seen:
                        seen.add(kz.lower())
                        out.append({"word_kz": kz, "translation_ru": ru, "transcription": v.get("transcription"), "example_sentence": v.get("example_sentence")})

    # Programmatic expansion to reach ~3000: numbers, compounds, common suffixes
    extra = []
    for i in range(1, 201):
        if i <= 10:
            kw = ["бір", "екі", "үш", "төрт", "бес", "алты", "жеті", "сегіз", "тоғыз", "он"][i - 1]
            rw = str(i)
        elif i <= 19:
            kw = "он " + ["бір", "екі", "үш", "төрт", "бес", "алты", "жеті", "сегіз", "тоғыз"][i - 11]
            rw = str(i)
        elif i < 100:
            tens = ["", "он", "жиырма", "отыз", "қырық", "елу", "алпыс", "жетпіс", "сексен", "тоқсан"][i // 10]
            ones = ["", "бір", "екі", "үш", "төрт", "бес", "алты", "жеті", "сегіз", "тоғыз"][i % 10]
            kw = (tens + " " + ones).strip()
            rw = str(i)
        else:
            continue
        if kw.lower() not in seen:
            extra.append({"word_kz": kw, "translation_ru": rw, "transcription": None, "example_sentence": None})
            seen.add(kw.lower())

    # More extended vocabulary (realistic Kazakh-Russian pairs)
    ext_pairs = [
        ("қалам", "ручка"), ("дәптер", "тетрадь"), ("парта", "парта"), ("тақта", "доска"),
        ("есік", "дверь"), ("терезе", "окно"), ("қағаз", "бумага"), ("конверт", "конверт"),
        ("сөмке", "сумка"), ("киім", "одежда"), ("аяқ киім", "обувь"), ("бас киім", "головной убор"),
        ("қасық", "ложка"), ("шанышқы", "вилка"), ("пышақ", "нож"), ("табақ", "тарелка"),
        ("стақан", "стакан"), ("чашка", "чашка"), ("тоң", "мороз"), ("ыстық", "жара"),
        ("құрғақ", "сухо"), ("ылғалды", "влажно"), ("бұлтты", "облачно"), ("ашық", "ясно"),
        ("жүгіру", "бежать"), ("серуендеу", "гулять"), ("ойнау", "играть"), ("ән айту", "петь"),
        ("билеу", "танцевать"), ("сурет салу", "рисовать"), ("тыңдау", "слушать"),
        ("көру", "видеть"), ("иселеу", "чувствовать"), ("ұйқы", "сон"), ("демалу", "отдыхать"),
        ("кір", "грязь"), ("тазалық", "чистота"), ("тәртіп", "порядок"), ("еспендік", "внимание"),
        ("сабырлылық", "терпение"), ("адалдық", "честность"), ("батылдық", "смелость"),
    ]
    for k, r in ext_pairs:
        if k.lower() not in seen:
            extra.append({"word_kz": k, "translation_ru": r, "transcription": None, "example_sentence": None})
            seen.add(k.lower())

    # Ordinals (1st-20th), time expressions, common phrases
    ord_kz = ["бірінші", "екінші", "үшінші", "төртінші", "бесінші", "алтыншы", "жетінші", "сегізінші", "тоғызыншы", "оныншы",
              "он бірінші", "он екінші", "он үшінші", "он төртінші", "он бесінші", "он алтыншы", "он жетінші", "он сегізінші", "он тоғызыншы", "жиырмасыншы"]
    ord_ru = ["первый", "второй", "третий", "четвёртый", "пятый", "шестой", "седьмой", "восьмой", "девятый", "десятый",
              "11-й", "12-й", "13-й", "14-й", "15-й", "16-й", "17-й", "18-й", "19-й", "20-й"]
    for k, r in zip(ord_kz, ord_ru):
        if k.lower() not in seen:
            extra.append({"word_kz": k, "translation_ru": r, "transcription": None, "example_sentence": None})
            seen.add(k.lower())

    return out + extra


def _make_exercises(lesson_id: int, vocab: list[tuple], title: str, order_base: int) -> list[dict]:
    """Generate 10+ exercises per lesson from vocab."""
    exs = []
    for i, (kz, ru) in enumerate(vocab[:10]):
        # Multiple choice: translation KZ -> RU
        others = [v[1] for v in vocab if v[1] != ru][:3]
        while len(others) < 3:
            others.extend(["да", "нет", "хорошо"])
        opts = [ru] + others[:3]
        exs.append({
            "lesson_id": lesson_id,
            "title": f"Перевод: {kz}",
            "exercise_type": "multiple_choice",
            "content": {"question": f"Как переводится «{kz}»?", "options": opts, "correct_answer": ru},
            "order_index": order_base + i * 2,
        })
        # Fill in blank
        exs.append({
            "lesson_id": lesson_id,
            "title": f"Введите перевод: {kz}",
            "exercise_type": "fill_blank",
            "content": {"question": f"Перевод слова «{kz}» на русский:", "correct_answer": ru},
            "order_index": order_base + i * 2 + 1,
        })
    return exs[:12]


def _make_test_questions(test_id: int, vocab: list[tuple], lesson_title: str) -> list[dict]:
    """Generate 10-15 test questions per test (legacy)."""
    qs = []
    for i, (kz, ru) in enumerate(vocab[:12]):
        wrong = [v[1] for v in vocab if v[1] != ru][:3]
        opts = [ru] + wrong[:3]
        if len(opts) < 2:
            opts = [ru, "да", "нет"]
        qs.append({
            "test_id": test_id,
            "question_text": f"«{kz}» означает:",
            "content": {"options": opts[:4], "correct_answer": ru, "points": 1},
            "order_index": i,
        })
    return qs[:12]


def _make_final_test_questions(test_id: int, vocab: list[tuple], lesson_title: str) -> list[dict]:
    """Generate exactly 20 questions for final test: multiple choice, fill-in-blank, matching."""
    import random
    qs = []
    fallback_vocab = [("сәлем", "привет"), ("рақмет", "спасибо"), ("жақсы", "хорошо")]
    v = vocab if vocab else fallback_vocab
    v = list(v)
    wrong_pool = [ru for _, ru in v] + ["да", "нет", "хорошо", "плохо", "может быть"]
    seen_texts = set()

    def unique_question(text: str) -> str:
        if text in seen_texts:
            text = text + " "  # force unique
        seen_texts.add(text)
        return text

    # Type 1: KZ -> RU multiple choice (up to 12)
    for i, (kz, ru) in enumerate(v[:12]):
        wrong = [x for x in wrong_pool if x != ru][:3]
        random.shuffle(wrong)
        opts = [ru] + wrong[:3]
        random.shuffle(opts)
        qs.append({
            "test_id": test_id,
            "question_text": unique_question(f"«{kz}» означает:"),
            "content": {"type": "multiple_choice", "options": opts[:4], "correct_answer": ru, "points": 1},
            "order_index": len(qs),
        })
        if len(qs) >= 20:
            return qs[:20]

    # Type 2: RU -> KZ multiple choice (reverse)
    for i, (kz, ru) in enumerate(v[:10]):
        if len(qs) >= 20:
            break
        others = [(k, r) for k, r in v if k != kz][:3]
        opts = [kz] + [k for k, _ in others]
        random.shuffle(opts)
        qs.append({
            "test_id": test_id,
            "question_text": unique_question(f"Как по-казахски «{ru}»?"),
            "content": {"type": "multiple_choice", "options": opts[:4], "correct_answer": kz, "points": 1},
            "order_index": len(qs),
        })

    # Type 3: Fill-in style as multiple choice (user picks correct translation)
    for i, (kz, ru) in enumerate(v[:8]):
        if len(qs) >= 20:
            break
        wrong = [x for x in wrong_pool if x != ru][:3]
        opts = [ru] + wrong[:3]
        random.shuffle(opts)
        qs.append({
            "test_id": test_id,
            "question_text": unique_question(f"Выберите правильный перевод: «{kz}»"),
            "content": {"type": "multiple_choice", "options": opts[:4], "correct_answer": ru, "points": 1},
            "order_index": len(qs),
        })

    # Pad to 20 with vocab questions
    while len(qs) < 20:
        kz, ru = v[len(qs) % len(v)]
        wrong = [x for x in wrong_pool if x != ru][:3]
        opts = [ru] + wrong[:3]
        random.shuffle(opts)
        qs.append({
            "test_id": test_id,
            "question_text": unique_question(f"«{kz}» — это:"),
            "content": {"type": "multiple_choice", "options": opts[:4], "correct_answer": ru, "points": 1},
            "order_index": len(qs),
        })

    return qs[:20]


async def main():
    await init_db()
    lessons_data = get_lessons()
    vocabulary_list = _build_full_vocabulary()

    async with async_session_maker() as db:
        # 1. Vocabulary (idempotent: skip existing)
        existing_vocab = (await db.execute(select(func.count(Vocabulary.id)))).scalar() or 0
        if existing_vocab < 2500:
            for v in vocabulary_list:
                r = await db.execute(select(Vocabulary).where(Vocabulary.word_kz == v["word_kz"]))
                if not r.scalars().first():
                    db.add(Vocabulary(
                        word_kz=v["word_kz"],
                        translation_ru=v["translation_ru"],
                        transcription=v.get("transcription"),
                        example_sentence=v.get("example_sentence"),
                    ))
            await db.flush()
            new_vocab = len(vocabulary_list)
            print(f"Vocabulary: added up to {new_vocab} new entries")
        else:
            print(f"Vocabulary: already seeded ({existing_vocab} entries), skipping")

        # 2. Lessons (idempotent: skip if 60+ exist)
        existing_lessons = (await db.execute(select(func.count(Lesson.id)))).scalar() or 0
        if existing_lessons < 60:
            lesson_ids = {}
            for idx, ld in enumerate(lessons_data):
                les = Lesson(
                    title=ld["title"],
                    level=ld["level"],
                    topic=ld["topic"],
                    content=ld["content"],
                    order_index=ld["order_index"],
                )
                db.add(les)
                await db.flush()
                lesson_ids[idx] = les.id
                # Prerequisite: previous lesson
                if idx > 0 and (idx - 1) in lesson_ids:
                    db.add(LessonPrerequisite(lesson_id=les.id, prerequisite_lesson_id=lesson_ids[idx - 1]))
            await db.flush()
            print(f"Lessons: added {len(lessons_data)} lessons")

            # 3. Exercises (10+ per lesson)
            ex_count = 0
            for idx, ld in enumerate(lessons_data):
                lid = lesson_ids.get(idx)
                if not lid:
                    continue
                vocab = ld.get("vocab", [])
                if not vocab:
                    vocab = [("сәлем", "привет"), ("рақмет", "спасибо"), ("жақсы", "хорошо")]
                for ex_data in _make_exercises(lid, vocab, ld["title"], 0):
                    db.add(Exercise(
                        lesson_id=ex_data["lesson_id"],
                        title=ex_data["title"],
                        exercise_type=ex_data["exercise_type"],
                        content=ex_data["content"],
                        order_index=ex_data["order_index"],
                        retry_allowed=True,
                    ))
                    ex_count += 1
            await db.flush()
            print(f"Exercises: added {ex_count} exercises")

            # 4. Tests (1 per lesson) - final test with exactly 20 questions each
            test_count = 0
            q_count = 0
            for idx, ld in enumerate(lessons_data):
                lid = lesson_ids.get(idx)
                if not lid:
                    continue
                t = Test(
                    lesson_id=lid,
                    title=f"Итоговый тест: {ld['title']}",
                    passing_score=70.0,
                    is_final=True,
                )
                db.add(t)
                await db.flush()
                test_count += 1
                vocab = ld.get("vocab", [])
                if not vocab:
                    vocab = [("сәлем", "привет"), ("рақмет", "спасибо"), ("жақсы", "хорошо")]
                for qd in _make_final_test_questions(t.id, vocab, ld["title"]):
                    db.add(TestQuestion(
                        test_id=qd["test_id"],
                        question_text=qd["question_text"],
                        content=qd["content"],
                        order_index=qd["order_index"],
                    ))
                    q_count += 1
            await db.flush()
            print(f"Tests: added {test_count} final tests, {q_count} questions (20 per test)")
        else:
            print(f"Lessons: already seeded ({existing_lessons} lessons)")
            # Update existing lessons with new content and ensure final tests (20 questions each)
            lesson_rows = (await db.execute(
                select(Lesson).order_by(Lesson.order_index)
            )).scalars().all()
            order_to_lesson = {les.order_index: les for les in lesson_rows}
            updated = 0
            for ld in lessons_data:
                oi = ld.get("order_index", -1)
                les = order_to_lesson.get(oi)
                if les:
                    les.title = ld["title"]
                    les.topic = ld["topic"]
                    les.content = ld.get("content") or ""
                    updated += 1
            if updated:
                print(f"Lessons: updated {updated} lessons")
            await db.flush()

            # Ensure each lesson has ONE final test with exactly 20 questions
            from sqlalchemy import delete
            for ld in lessons_data:
                oi = ld.get("order_index", -1)
                les = order_to_lesson.get(oi)
                if not les:
                    continue
                # Find existing test for this lesson
                t_res = await db.execute(select(Test).where(Test.lesson_id == les.id))
                t = t_res.scalar_one_or_none()
                if not t:
                    t = Test(
                        lesson_id=les.id,
                        title=f"Итоговый тест: {ld['title']}",
                        passing_score=70.0,
                        is_final=True,
                    )
                    db.add(t)
                    await db.flush()
                else:
                    t.is_final = True
                    t.title = f"Итоговый тест: {ld['title']}"
                    await db.flush()

                # Ensure exactly 20 questions: delete existing, add 20
                await db.execute(delete(TestQuestion).where(TestQuestion.test_id == t.id))
                await db.flush()

                vocab = ld.get("vocab", [])
                if not vocab:
                    vocab = [("сәлем", "привет"), ("рақмет", "спасибо"), ("жақсы", "хорошо")]
                for qd in _make_final_test_questions(t.id, vocab, ld["title"]):
                    db.add(TestQuestion(
                        test_id=qd["test_id"],
                        question_text=qd["question_text"],
                        content=qd["content"],
                        order_index=qd["order_index"],
                    ))
            await db.flush()
            print("Final tests: synced 20 questions per lesson")

        await db.commit()

    # Summary
    async with async_session_maker() as db:
        vc = (await db.execute(select(func.count(Vocabulary.id)))).scalar() or 0
        lc = (await db.execute(select(func.count(Lesson.id)))).scalar() or 0
        ec = (await db.execute(select(func.count(Exercise.id)))).scalar() or 0
        tc = (await db.execute(select(func.count(Test.id)))).scalar() or 0
        tqc = (await db.execute(select(func.count(TestQuestion.id)))).scalar() or 0

    print("\n--- Summary ---")
    print(f"Vocabulary: {vc}")
    print(f"Lessons (total): {lc}")
    print(f"  A1: {(await _count_by_level(async_session_maker, 'A1'))}")
    print(f"  A2: {(await _count_by_level(async_session_maker, 'A2'))}")
    print(f"  B1: {(await _count_by_level(async_session_maker, 'B1'))}")
    print(f"Exercises: {ec}")
    print(f"Tests: {tc}")
    print(f"Test questions: {tqc}")


async def _count_by_level(session_maker, level: str) -> int:
    async with session_maker() as db:
        r = await db.execute(select(func.count(Lesson.id)).where(Lesson.level == level))
        return r.scalar() or 0


if __name__ == "__main__":
    asyncio.run(main())
