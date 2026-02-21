"""Auth business logic."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User

from app.auth.schemas import UserRegister, UserLogin


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    """Register new user."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ValueError("Email already registered")
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, data: UserLogin) -> User | None:
    """Authenticate user by email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(data.password, user.hashed_password):
        return None
    return user


def create_token_for_user(user: User) -> str:
    """Create JWT for user."""
    return create_access_token(data={"sub": str(user.id)})
