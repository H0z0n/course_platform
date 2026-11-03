from fastapi import APIRouter, HTTPException, status
from sqlalchemy import distinct, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import OptionalUser, SessionDep, StaffUser
from app.models import Course, Lesson, Module, Purchase, QuizQuestion
from app.schemas.common import ReorderRequest
from app.schemas.course import CourseCard, CourseCreate, CourseOutline, CourseRead, CourseUpdate
from app.schemas.module import ModuleCreate, ModuleRead
from app.services.common import get_or_404
from app.services.ordering import apply_order, next_position
from app.services.outline import OUTLINE_LOAD_OPTIONS, build_course_outline

router = APIRouter(prefix="/courses", tags=["courses"])


async def ensure_slug_free(session: AsyncSession, slug: str) -> None:
    taken = await session.scalar(select(exists().where(Course.slug == slug)))
    if taken:
        raise HTTPException(status.HTTP_409_CONFLICT, "Курс с таким slug уже есть")


@router.get("", response_model=list[CourseCard])
async def list_courses(session: SessionDep):
    courses = (await session.scalars(select(Course).order_by(Course.id))).all()
    rows = await session.execute(
        select(
            Module.course_id,
            func.count(distinct(Module.id)),
            func.count(Lesson.id),
            func.count(Lesson.id).filter(Lesson.is_free_preview),
            func.coalesce(func.sum(Lesson.duration_minutes), 0),
        )
        .select_from(Module)
        .outerjoin(Lesson, Lesson.module_id == Module.id)
        .group_by(Module.course_id)
    )
    stats = {course_id: values for course_id, *values in rows}
    question_rows = await session.execute(
        select(Module.course_id, func.count(QuizQuestion.id))
        .select_from(QuizQuestion)
        .join(Lesson, QuizQuestion.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .group_by(Module.course_id)
    )
    questions = {course_id: count for course_id, count in question_rows}
    cards = []
    for course in courses:
        module_count, lesson_count, free_count, minutes = stats.get(course.id, (0, 0, 0, 0))
        cards.append(
            CourseCard(
                **CourseRead.model_validate(course).model_dump(),
                module_count=module_count,
                lesson_count=lesson_count,
                free_lesson_count=free_count,
                total_minutes=minutes,
                question_count=questions.get(course.id, 0),
            )
        )
    return cards


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate, session: SessionDep, user: StaffUser):
    await ensure_slug_free(session, payload.slug)
    course = Course(**payload.model_dump(), owner_id=user.id)
    session.add(course)
    await session.commit()
    return course


@router.get("/by-slug/{slug}", response_model=CourseOutline)
async def get_course_by_slug(slug: str, session: SessionDep, user: OptionalUser):
    course = await session.scalar(
        select(Course).where(Course.slug == slug).options(OUTLINE_LOAD_OPTIONS)
    )
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Курс не найден")
    return await build_course_outline(session, course, user)


@router.get("/{course_id}", response_model=CourseOutline)
async def get_course(course_id: int, session: SessionDep, user: OptionalUser):
    course = await session.scalar(
        select(Course).where(Course.id == course_id).options(OUTLINE_LOAD_OPTIONS)
    )
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Курс не найден")
    return await build_course_outline(session, course, user)


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int, payload: CourseUpdate, session: SessionDep, _: StaffUser
):
    course = await get_or_404(session, Course, course_id, "Курс не найден")
    updates = payload.model_dump(exclude_unset=True)
    if "slug" in updates and updates["slug"] != course.slug:
        await ensure_slug_free(session, updates["slug"])
    for field, value in updates.items():
        setattr(course, field, value)
    await session.commit()
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: int, session: SessionDep, _: StaffUser):
    course = await get_or_404(session, Course, course_id, "Курс не найден")
    course_module_ids = select(Module.id).where(Module.course_id == course_id)
    has_purchases = await session.scalar(
        select(
            exists().where(
                or_(Purchase.course_id == course_id, Purchase.module_id.in_(course_module_ids))
            )
        )
    )
    if has_purchases:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Этот курс или его модули уже покупали — удалить нельзя"
        )
    await session.delete(course)
    await session.commit()


@router.get("/{course_id}/modules", response_model=list[ModuleRead])
async def list_modules(course_id: int, session: SessionDep):
    await get_or_404(session, Course, course_id, "Курс не найден")
    modules = await session.scalars(
        select(Module).where(Module.course_id == course_id).order_by(Module.position, Module.id)
    )
    return modules.all()


@router.post(
    "/{course_id}/modules", response_model=ModuleRead, status_code=status.HTTP_201_CREATED
)
async def create_module(
    course_id: int, payload: ModuleCreate, session: SessionDep, _: StaffUser
):
    await get_or_404(session, Course, course_id, "Курс не найден")
    position = payload.position
    if position is None:
        position = await next_position(session, Module.position, Module.course_id == course_id)
    module = Module(course_id=course_id, title=payload.title, price=payload.price, position=position)
    session.add(module)
    await session.commit()
    return module


@router.put("/{course_id}/modules/order", response_model=list[ModuleRead])
async def reorder_modules(
    course_id: int, payload: ReorderRequest, session: SessionDep, _: StaffUser
):
    await get_or_404(session, Course, course_id, "Курс не найден")
    modules = (await session.scalars(select(Module).where(Module.course_id == course_id))).all()
    ordered = apply_order(modules, payload.ids)
    await session.commit()
    return ordered
