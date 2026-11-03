from fastapi import APIRouter, HTTPException, status
from sqlalchemy import exists, select

from app.dependencies import OptionalUser, SessionDep, StaffUser
from app.models import Lesson, Module, Purchase
from app.schemas.common import ReorderRequest
from app.schemas.lesson import LessonCreate, LessonOutline, LessonRead, LessonSummary
from app.schemas.module import ModuleRead, ModuleUpdate
from app.services.access import get_course_access
from app.services.common import get_or_404
from app.services.ordering import apply_order, next_position
from app.services.outline import lesson_outline
from app.services.quiz import count_questions

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("/{module_id}", response_model=ModuleRead)
async def get_module(module_id: int, session: SessionDep):
    return await get_or_404(session, Module, module_id, "Модуль не найден")


@router.patch("/{module_id}", response_model=ModuleRead)
async def update_module(
    module_id: int, payload: ModuleUpdate, session: SessionDep, _: StaffUser
):
    module = await get_or_404(session, Module, module_id, "Модуль не найден")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(module, field, value)
    await session.commit()
    return module


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(module_id: int, session: SessionDep, _: StaffUser):
    module = await get_or_404(session, Module, module_id, "Модуль не найден")
    has_purchases = await session.scalar(select(exists().where(Purchase.module_id == module_id)))
    if has_purchases:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Этот модуль уже покупали — удалить нельзя"
        )
    await session.delete(module)
    await session.commit()


@router.get("/{module_id}/lessons", response_model=list[LessonOutline])
async def list_lessons(module_id: int, session: SessionDep, user: OptionalUser):
    module = await get_or_404(session, Module, module_id, "Модуль не найден")
    access = await get_course_access(session, user, module.course_id)
    lessons = (
        await session.scalars(
            select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.position, Lesson.id)
        )
    ).all()
    questions = await count_questions(session, [lesson.id for lesson in lessons])
    return [lesson_outline(lesson, access, questions.get(lesson.id, 0)) for lesson in lessons]


@router.post(
    "/{module_id}/lessons", response_model=LessonRead, status_code=status.HTTP_201_CREATED
)
async def create_lesson(
    module_id: int, payload: LessonCreate, session: SessionDep, _: StaffUser
):
    await get_or_404(session, Module, module_id, "Модуль не найден")
    position = payload.position
    if position is None:
        position = await next_position(session, Lesson.position, Lesson.module_id == module_id)
    lesson = Lesson(
        module_id=module_id,
        title=payload.title,
        content_type=payload.content_type,
        content=payload.content,
        is_free_preview=payload.is_free_preview,
        duration_minutes=payload.duration_minutes,
        position=position,
    )
    session.add(lesson)
    await session.commit()
    return lesson


@router.put("/{module_id}/lessons/order", response_model=list[LessonSummary])
async def reorder_lessons(
    module_id: int, payload: ReorderRequest, session: SessionDep, _: StaffUser
):
    await get_or_404(session, Module, module_id, "Модуль не найден")
    lessons = (await session.scalars(select(Lesson).where(Lesson.module_id == module_id))).all()
    ordered = apply_order(lessons, payload.ids)
    await session.commit()
    return ordered
