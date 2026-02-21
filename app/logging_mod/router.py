"""Logs API routes (admin only)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, RequireAdmin
from app.models.user import User
from app.models.log import Log

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/")
async def list_logs(
    current_user: Annotated[User, RequireAdmin],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    """List action logs (admin only)."""
    result = await db.execute(
        select(Log).order_by(Log.created_at.desc()).limit(limit).offset(offset)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "details": l.details,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
