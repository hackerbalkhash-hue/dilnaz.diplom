"""Lesson business logic."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson, LessonPrerequisite, LessonCompletion
from app.models.user import User
from app.lessons.schemas import LessonCreate, LessonUpdate


async def get_lesson_for_assistant(
    db: AsyncSession, lesson_id: int
) -> dict | None:
    """Fetch lesson content for assistant. Returns id, title, topic, content."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        return None
    return _lesson_to_dict(lesson)


def _lesson_to_dict(lesson: Lesson) -> dict:
    """Map Lesson ORM to assistant dict."""
    return {
        "id": lesson.id,
        "title": lesson.title,
        "topic": lesson.topic,
        "content": lesson.content or "",
    }


async def get_lesson_by_order_index(
    db: AsyncSession, order_index_1based: int
) -> dict | None:
    """
    Get lesson by 1-based order index (user says "1 урок" = first, "2 урок" = second).
    Orders by order_index (NULLs last via coalesce), then by id.
    Fallback: if no row by order, take N-th lesson by id (for DBs where order_index not set).
    """
    # Prefer order by order_index (NULLs last so they don't take first positions)
    result = await db.execute(
        select(Lesson).order_by(
            func.coalesce(Lesson.order_index, 999999),
            Lesson.id,
        ).offset(order_index_1based - 1).limit(1)
    )
    lesson = result.scalar_one_or_none()
    if lesson:
        return _lesson_to_dict(lesson)
    # Fallback: N-th lesson by id (when order_index is missing or out of range)
    result = await db.execute(
        select(Lesson).order_by(Lesson.id).offset(order_index_1based - 1).limit(1)
    )
    lesson = result.scalar_one_or_none()
    if lesson:
        return _lesson_to_dict(lesson)
    return None


async def get_completed_lesson_ids(db: AsyncSession, user_id: int) -> set[int]:
    """Get set of lesson IDs completed by user."""
    result = await db.execute(
        select(LessonCompletion.lesson_id).where(
            LessonCompletion.user_id == user_id
        )
    )
    return set(row[0] for row in result.all())


async def get_prerequisites_map(db: AsyncSession) -> dict[int, list[int]]:
    """Map lesson_id -> [prerequisite_lesson_ids]."""
    result = await db.execute(
        select(LessonPrerequisite.lesson_id, LessonPrerequisite.prerequisite_lesson_id)
    )
    mapping: dict[int, list[int]] = {}
    for lesson_id, prereq_id in result.all():
        if lesson_id not in mapping:
            mapping[lesson_id] = []
        mapping[lesson_id].append(prereq_id)
    return mapping


def lesson_is_accessible(
    lesson_id: int,
    completed_ids: set[int],
    prereq_map: dict[int, list[int]],
) -> tuple[bool, list[int]]:
    """Check if lesson is accessible. Returns (is_accessible, prerequisite_ids)."""
    prereqs = prereq_map.get(lesson_id, [])
    if not prereqs:
        return True, []
    all_done = all(pid in completed_ids for pid in prereqs)
    return all_done, prereqs


async def create_lesson(db: AsyncSession, data: LessonCreate) -> Lesson:
    """Create lesson with prerequisites."""
    lesson = Lesson(
        title=data.title,
        level=data.level,
        topic=data.topic,
        content=data.content,
        order_index=data.order_index,
    )
    db.add(lesson)
    await db.flush()
    for pid in data.prerequisite_ids:
        db.add(LessonPrerequisite(lesson_id=lesson.id, prerequisite_lesson_id=pid))
    await db.flush()
    await db.refresh(lesson)
    return lesson


async def update_lesson(
    db: AsyncSession, lesson: Lesson, data: LessonUpdate
) -> Lesson:
    """Update lesson."""
    if data.title is not None:
        lesson.title = data.title
    if data.level is not None:
        lesson.level = data.level
    if data.topic is not None:
        lesson.topic = data.topic
    if data.content is not None:
        lesson.content = data.content
    if data.order_index is not None:
        lesson.order_index = data.order_index
    if data.prerequisite_ids is not None:
        existing = (
            await db.execute(
                select(LessonPrerequisite).where(
                    LessonPrerequisite.lesson_id == lesson.id
                )
            )
        ).scalars().all()
        for lp in existing:
            await db.delete(lp)
        for pid in data.prerequisite_ids:
            db.add(LessonPrerequisite(lesson_id=lesson.id, prerequisite_lesson_id=pid))
    await db.flush()
    await db.refresh(lesson)
    return lesson


async def complete_lesson(db: AsyncSession, user_id: int, lesson_id: int) -> None:
    """Mark lesson as completed for user."""
    existing = await db.execute(
        select(LessonCompletion).where(
            LessonCompletion.user_id == user_id,
            LessonCompletion.lesson_id == lesson_id,
        )
    )
    if existing.scalar_one_or_none():
        return
    db.add(LessonCompletion(user_id=user_id, lesson_id=lesson_id))
    await db.flush()


async def get_next_lesson(
    db: AsyncSession, lesson_id: int, completed_ids: set[int], prereq_map: dict[int, list[int]]
) -> dict | None:
    """
    Get next lesson in curriculum order.
    Returns dict with: next_lesson_id, title, level, is_accessible, locked_reason.
    """
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    current = result.scalar_one_or_none()
    if not current:
        return None

    # All lessons ordered by level (A1 < A2 < B1), order_index, id
    level_order = {"A1": 0, "A2": 1, "B1": 2}
    all_result = await db.execute(
        select(Lesson).order_by(Lesson.order_index, Lesson.id)
    )
    lessons = all_result.scalars().all()

    found_current = False
    for les in lessons:
        if les.id == lesson_id:
            found_current = True
            continue
        if not found_current:
            continue
        # This is the next lesson by order
        accessible, prereqs = lesson_is_accessible(les.id, completed_ids, prereq_map)
        locked_reason = None
        if not accessible and prereqs:
            missing = [p for p in prereqs if p not in completed_ids]
            locked_reason = f"Сначала пройдите уроки: {', '.join(str(x) for x in missing)}"
        return {
            "next_lesson_id": les.id,
            "title": les.title,
            "level": les.level,
            "is_accessible": accessible,
            "locked_reason": locked_reason,
        }

    # No next in same level - check first lesson of next level
    next_level_order = level_order.get(current.level, -1) + 1
    for les in lessons:
        if level_order.get(les.level, 99) == next_level_order:
            accessible, prereqs = lesson_is_accessible(les.id, completed_ids, prereq_map)
            locked_reason = None
            if not accessible and prereqs:
                locked_reason = "Сначала пройдите предыдущий уровень"
            return {
                "next_lesson_id": les.id,
                "title": les.title,
                "level": les.level,
                "is_accessible": accessible,
                "locked_reason": locked_reason,
            }

    return None
