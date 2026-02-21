"""
Create admin user. Run: python -m scripts.create_admin
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole


async def main():
    await init_db()
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return
        user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrator",
            role=UserRole.ADMIN,
        )
        db.add(user)
        await db.commit()
        print("Admin created: admin@example.com / admin123")


if __name__ == "__main__":
    asyncio.run(main())
