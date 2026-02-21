"""Action logging service."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log


async def log_action(
    db: AsyncSession,
    user_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> None:
    """Log user action to database."""
    log = Log(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log)
    await db.flush()
