from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.common import HttpUrlText, Money, PatchModel, Slug, Title
from app.schemas.lesson import LessonOutline


class CourseCreate(BaseModel):
    title: Title
    slug: Slug
    price: Money | None = None
    description: str = ""
    cover_image_url: HttpUrlText | None = None


class CourseUpdate(PatchModel):
    nullable_fields = frozenset({"price", "cover_image_url"})

    title: Title | None = None
    slug: Slug | None = None
    price: Money | None = None
    description: str | None = None
    cover_image_url: HttpUrlText | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    price: Decimal | None
    description: str
    cover_image_url: str | None
    owner_id: int


class CourseCard(CourseRead):
    module_count: int
    lesson_count: int
    free_lesson_count: int
    total_minutes: int
    question_count: int


class ModuleOutline(BaseModel):
    id: int
    title: str
    position: int
    price: Decimal | None
    is_purchased: bool
    lessons: list[LessonOutline]


class CourseOutline(CourseRead):
    is_purchased: bool
    modules: list[ModuleOutline]
