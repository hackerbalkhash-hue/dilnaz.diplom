"""User profile API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.users.schemas import UserProfile, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user profile."""
    return current_user


@router.patch("/me", response_model=UserProfile)
async def update_me(
    data: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user profile."""
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.language_level is not None:
        current_user.language_level = data.language_level
    if data.interface_language is not None:
        current_user.interface_language = data.interface_language
    await db.flush()
    await db.refresh(current_user)
    return current_user
