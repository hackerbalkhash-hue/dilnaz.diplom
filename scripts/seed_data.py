"""
Seed sample data for development. Run: python -m scripts.seed_data
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.lesson import Lesson
from app.models.exercise import Exercise
from app.models.test import Test, TestQuestion


async def main():
    await init_db()
    async with async_session_maker() as db:
        # Admin
        r = await db.execute(select(User).where(User.email == "admin@example.com"))
        if not r.scalar_one_or_none():
            db.add(User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator",
                role=UserRole.ADMIN,
            ))
            await db.flush()
            print("Admin: admin@example.com / admin123")

        # Sample lesson
        r = await db.execute(select(Lesson).limit(1))
        if not r.scalar_one_or_none():
            l1 = Lesson(
                title="Приветствия",
                level="A1",
                topic="Базовые фразы",
                content="Сәлем - Привет\nСәлеметсіз бе - Здравствуйте\nРақмет - Спасибо\nҚалыңыз қалай? - Как дела?",
                order_index=0,
            )
            db.add(l1)
            await db.flush()
            # Exercise
            ex = Exercise(
                lesson_id=l1.id,
                title="Выберите правильный перевод",
                exercise_type="multiple_choice",
                content={
                    "question": "Как будет 'Привет' на казахском?",
                    "options": ["Сәлем", "Рақмет", "Қош"],
                    "correct_answer": "Сәлем",
                },
                retry_allowed=True,
            )
            db.add(ex)
            # Test
            t = Test(lesson_id=l1.id, title="Тест: Приветствия", passing_score=70)
            db.add(t)
            await db.flush()
            db.add(TestQuestion(
                test_id=t.id,
                question_text="Сәлем означает:",
                content={"options": ["Привет", "Спасибо", "Пока"], "correct_answer": "Привет", "points": 1},
            ))
            print("Sample lesson, exercise, test created")
        await db.commit()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
