from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Course, Lesson, Module, User
from app.schemas.course import CourseOutline, ModuleOutline
from app.schemas.lesson import LessonOutline
from app.services.access import CourseAccess, get_course_access
from app.services.quiz import count_questions

OUTLINE_LOAD_OPTIONS = selectinload(Course.modules).selectinload(Module.lessons)


def lesson_outline(lesson: Lesson, access: CourseAccess, question_count: int) -> LessonOutline:
    return LessonOutline(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        content_type=lesson.content_type,
        position=lesson.position,
        is_free_preview=lesson.is_free_preview,
        duration_minutes=lesson.duration_minutes,
        is_open=access.can_open(lesson),
        question_count=question_count,
    )


async def build_course_outline(
    session: AsyncSession, course: Course, user: User | None
) -> CourseOutline:
    access = await get_course_access(session, user, course.id)
    lesson_ids = [lesson.id for module in course.modules for lesson in module.lessons]
    questions = await count_questions(session, lesson_ids)
    return CourseOutline(
        id=course.id,
        title=course.title,
        slug=course.slug,
        price=course.price,
        description=course.description,
        cover_image_url=course.cover_image_url,
        owner_id=course.owner_id,
        is_purchased=access.course_purchased,
        modules=[
            ModuleOutline(
                id=module.id,
                title=module.title,
                position=module.position,
                price=module.price,
                is_purchased=module.id in access.purchased_module_ids,
                lessons=[
                    lesson_outline(lesson, access, questions.get(lesson.id, 0))
                    for lesson in module.lessons
                ],
            )
            for module in course.modules
        ],
    )
