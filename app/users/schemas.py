"""User schemas."""
from pydantic import BaseModel, EmailStr
from app.models.user import LanguageLevel, InterfaceLanguage, UserRole


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    language_level: LanguageLevel | None
    interface_language: InterfaceLanguage

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    language_level: LanguageLevel | None = None
    interface_language: InterfaceLanguage | None = None
