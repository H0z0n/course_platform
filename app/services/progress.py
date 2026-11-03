from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lesson, LessonProgress, Module


async def count_lessons(session: AsyncSession, course_ids: list[int]) -> dict[int, int]:
    rows = await session.execute(
        select(Module.course_id, func.count(Lesson.id))
        .select_from(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .where(Module.course_id.in_(course_ids))
        .group_by(Module.course_id)
    )
    return {course_id: count for course_id, count in rows}


async def count_completed_lessons(
    session: AsyncSession, user_id: int, course_ids: list[int]
) -> dict[int, int]:
    rows = await session.execute(
        select(Module.course_id, func.count(LessonProgress.id))
        .select_from(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .where(
            LessonProgress.user_id == user_id,
            LessonProgress.completed_at.is_not(None),
            Module.course_id.in_(course_ids),
        )
        .group_by(Module.course_id)
    )
    return {course_id: count for course_id, count in rows}


def percent(completed: int, total: int) -> int:
    return completed * 100 // total if total else 0
