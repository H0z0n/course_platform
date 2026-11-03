from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models import QuestionKind

OptionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Prompt = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class OptionIn(BaseModel):
    text: OptionText
    is_correct: bool = False


class QuestionIn(BaseModel):
    kind: QuestionKind
    prompt: Prompt
    explanation: str = ""
    options: list[OptionIn] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def check_options(self) -> Self:
        if self.kind == QuestionKind.TEXT:
            self.options = [option.model_copy(update={"is_correct": True}) for option in self.options]
            return self
        if len(self.options) < 2:
            raise ValueError("нужно хотя бы два варианта ответа")
        correct = sum(option.is_correct for option in self.options)
        if self.kind == QuestionKind.SINGLE and correct != 1:
            raise ValueError("в вопросе с одним вариантом должен быть ровно один правильный")
        if self.kind == QuestionKind.MULTIPLE and correct == 0:
            raise ValueError("отметьте хотя бы один правильный вариант")
        return self


class OptionAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    is_correct: bool


class QuestionAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    position: int
    kind: QuestionKind
    prompt: str
    explanation: str
    options: list[OptionAdmin]


class AnswerIn(BaseModel):
    option_ids: list[int] = Field(default_factory=list, max_length=20)
    text: str | None = Field(default=None, max_length=500)


class AnswerResult(BaseModel):
    question_id: int
    is_correct: bool
    option_ids: list[int]
    text: str | None
    correct_option_ids: list[int]
    accepted_answers: list[str]
    explanation: str
    answered_at: datetime


class OptionPublic(BaseModel):
    id: int
    text: str


class QuestionPublic(BaseModel):
    id: int
    position: int
    kind: QuestionKind
    prompt: str
    options: list[OptionPublic]
    result: AnswerResult | None
