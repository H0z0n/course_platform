from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


class ProgressUpdate(BaseModel):
    completed: bool


class LessonProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lesson_id: int
    completed_at: datetime | None

    @computed_field
    @property
    def completed(self) -> bool:
        return self.completed_at is not None


class CourseProgress(BaseModel):
    course_id: int
    total_lessons: int
    completed_lessons: int
    percent: int
    lessons: list[LessonProgressRead]


class MyCourse(BaseModel):
    course_id: int
    title: str
    slug: str
    has_purchase: bool
    total_lessons: int
    completed_lessons: int
    percent: int
