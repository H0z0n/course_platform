from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.models import ContentType
from app.schemas.common import Minutes, PatchModel, Position, Title, validate_lesson_content


class LessonCreate(BaseModel):
    title: Title
    content_type: ContentType = ContentType.TEXT
    content: str = ""
    is_free_preview: bool = False
    duration_minutes: Minutes | None = None
    position: Position | None = None

    @model_validator(mode="after")
    def check_content(self) -> Self:
        validate_lesson_content(self.content_type, self.content)
        return self


class LessonUpdate(PatchModel):
    nullable_fields = frozenset({"duration_minutes"})

    title: Title | None = None
    content_type: ContentType | None = None
    content: str | None = None
    is_free_preview: bool | None = None
    duration_minutes: Minutes | None = None
    position: Position | None = None
    module_id: int | None = None


class LessonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    title: str
    content_type: ContentType
    position: int
    is_free_preview: bool
    duration_minutes: int | None


class LessonOutline(LessonSummary):
    is_open: bool
    question_count: int


class LessonRead(LessonSummary):
    content: str
