from fastapi import APIRouter, HTTPException, status

from app.dependencies import OptionalUser, SessionDep, StaffUser
from app.models import Lesson, Module
from app.schemas.common import validate_lesson_content
from app.schemas.lesson import LessonRead, LessonUpdate
from app.services.access import ensure_can_open, get_course_access, get_lesson_with_course_id
from app.services.common import get_or_404
from app.services.ordering import next_position

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{lesson_id}", response_model=LessonRead)
async def get_lesson(lesson_id: int, session: SessionDep, user: OptionalUser):
    lesson, course_id = await get_lesson_with_course_id(session, lesson_id)
    access = await get_course_access(session, user, course_id)
    ensure_can_open(access, lesson, user)
    return lesson


@router.patch("/{lesson_id}", response_model=LessonRead)
async def update_lesson(
    lesson_id: int, payload: LessonUpdate, session: SessionDep, _: StaffUser
):
    lesson = await get_or_404(session, Lesson, lesson_id, "Урок не найден")
    updates = payload.model_dump(exclude_unset=True)

    new_module_id = updates.get("module_id", lesson.module_id)
    if new_module_id != lesson.module_id:
        await get_or_404(session, Module, new_module_id, "Модуль не найден")
        if "position" not in updates:
            updates["position"] = await next_position(
                session, Lesson.position, Lesson.module_id == new_module_id
            )

    try:
        validate_lesson_content(
            updates.get("content_type", lesson.content_type),
            updates.get("content", lesson.content),
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error

    for field, value in updates.items():
        setattr(lesson, field, value)
    await session.commit()
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(lesson_id: int, session: SessionDep, _: StaffUser):
    lesson = await get_or_404(session, Lesson, lesson_id, "Урок не найден")
    await session.delete(lesson)
    await session.commit()
