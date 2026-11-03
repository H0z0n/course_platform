from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, SessionDep
from app.models import Course, Lesson, LessonProgress, Module, Purchase, User
from app.schemas.progress import CourseProgress, LessonProgressRead, MyCourse, ProgressUpdate
from app.services.access import ensure_can_open, get_course_access, get_lesson_with_course_id
from app.services.common import get_or_404
from app.services.progress import count_completed_lessons, count_lessons, percent

router = APIRouter(tags=["progress"])


async def ensure_lesson_open(session: AsyncSession, lesson_id: int, user: User) -> None:
    lesson, course_id = await get_lesson_with_course_id(session, lesson_id)
    access = await get_course_access(session, user, course_id)
    ensure_can_open(access, lesson, user)


async def get_or_create_progress(
    session: AsyncSession, user_id: int, lesson_id: int
) -> LessonProgress:
    progress = await session.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id
        )
    )
    if progress is None:
        progress = LessonProgress(user_id=user_id, lesson_id=lesson_id, completed_at=None)
        session.add(progress)
    return progress


@router.post("/lessons/{lesson_id}/progress/start", response_model=LessonProgressRead)
async def start_lesson(lesson_id: int, session: SessionDep, user: CurrentUser):
    await ensure_lesson_open(session, lesson_id, user)
    progress = await get_or_create_progress(session, user.id, lesson_id)
    await session.commit()
    return progress


@router.put("/lessons/{lesson_id}/progress", response_model=LessonProgressRead)
async def set_lesson_progress(
    lesson_id: int, payload: ProgressUpdate, session: SessionDep, user: CurrentUser
):
    await ensure_lesson_open(session, lesson_id, user)
    progress = await get_or_create_progress(session, user.id, lesson_id)
    if not payload.completed:
        progress.completed_at = None
    elif progress.completed_at is None:
        progress.completed_at = datetime.now(UTC)
    await session.commit()
    return progress


@router.get("/courses/{course_id}/progress", response_model=CourseProgress)
async def course_progress(course_id: int, session: SessionDep, user: CurrentUser):
    await get_or_404(session, Course, course_id, "Курс не найден")
    total = (await count_lessons(session, [course_id])).get(course_id, 0)
    rows = (
        await session.scalars(
            select(LessonProgress)
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .join(Module, Lesson.module_id == Module.id)
            .where(LessonProgress.user_id == user.id, Module.course_id == course_id)
            .order_by(LessonProgress.lesson_id)
        )
    ).all()
    completed = sum(1 for row in rows if row.completed_at is not None)
    return CourseProgress(
        course_id=course_id,
        total_lessons=total,
        completed_lessons=completed,
        percent=percent(completed, total),
        lessons=[LessonProgressRead.model_validate(row) for row in rows],
    )


@router.get("/progress/me", response_model=list[MyCourse])
async def my_courses(session: SessionDep, user: CurrentUser):
    purchased_ids = set(
        await session.scalars(
            select(func.coalesce(Purchase.course_id, Module.course_id))
            .select_from(Purchase)
            .outerjoin(Module, Purchase.module_id == Module.id)
            .where(Purchase.user_id == user.id)
        )
    )
    started_ids = set(
        await session.scalars(
            select(Module.course_id)
            .select_from(LessonProgress)
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .join(Module, Lesson.module_id == Module.id)
            .where(LessonProgress.user_id == user.id)
        )
    )
    course_ids = list(purchased_ids | started_ids)
    if not course_ids:
        return []

    courses = await session.scalars(
        select(Course).where(Course.id.in_(course_ids)).order_by(Course.title)
    )
    totals = await count_lessons(session, course_ids)
    completed = await count_completed_lessons(session, user.id, course_ids)
    return [
        MyCourse(
            course_id=course.id,
            title=course.title,
            slug=course.slug,
            has_purchase=course.id in purchased_ids,
            total_lessons=totals.get(course.id, 0),
            completed_lessons=completed.get(course.id, 0),
            percent=percent(completed.get(course.id, 0), totals.get(course.id, 0)),
        )
        for course in courses
    ]
