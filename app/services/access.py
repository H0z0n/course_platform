from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import unauthorized
from app.models import STAFF_ROLES, Lesson, Module, Purchase, User


@dataclass(frozen=True)
class CourseAccess:
    is_staff: bool = False
    course_purchased: bool = False
    purchased_module_ids: frozenset[int] = frozenset()

    def can_open(self, lesson: Lesson) -> bool:
        return (
            lesson.is_free_preview
            or self.is_staff
            or self.course_purchased
            or lesson.module_id in self.purchased_module_ids
        )


async def get_course_access(
    session: AsyncSession, user: User | None, course_id: int
) -> CourseAccess:
    if user is None:
        return CourseAccess()

    rows = await session.execute(
        select(Purchase.course_id, Purchase.module_id)
        .outerjoin(Module, Purchase.module_id == Module.id)
        .where(Purchase.user_id == user.id)
        .where(or_(Purchase.course_id == course_id, Module.course_id == course_id))
    )
    course_purchased = False
    module_ids: set[int] = set()
    for purchased_course_id, purchased_module_id in rows:
        if purchased_course_id is not None:
            course_purchased = True
        else:
            module_ids.add(purchased_module_id)

    return CourseAccess(
        is_staff=user.role in STAFF_ROLES,
        course_purchased=course_purchased,
        purchased_module_ids=frozenset(module_ids),
    )


async def get_lesson_with_course_id(session: AsyncSession, lesson_id: int) -> tuple[Lesson, int]:
    row = (
        await session.execute(
            select(Lesson, Module.course_id).join(Lesson.module).where(Lesson.id == lesson_id)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Урок не найден")
    lesson, course_id = row
    return lesson, course_id


def ensure_can_open(access: CourseAccess, lesson: Lesson, user: User | None) -> None:
    if access.can_open(lesson):
        return
    if user is None:
        raise unauthorized("Войдите, чтобы открыть этот урок")
    raise HTTPException(
        status.HTTP_403_FORBIDDEN, "Урок откроется после покупки курса или модуля"
    )
