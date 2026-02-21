"""
User model - authentication and profile.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Enum as SQLEnum, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class LanguageLevel(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"


class InterfaceLanguage(str, Enum):
    KAZAKH = "kk"
    RUSSIAN = "ru"


class User(Base):
    """User account and profile."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.STUDENT
    )
    language_level: Mapped[LanguageLevel | None] = mapped_column(
        SQLEnum(LanguageLevel), nullable=True
    )
    interface_language: Mapped[InterfaceLanguage] = mapped_column(
        SQLEnum(InterfaceLanguage), default=InterfaceLanguage.RUSSIAN
    )

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
