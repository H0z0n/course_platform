from datetime import datetime
from typing import Self

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class PurchaseTarget(BaseModel):
    course_id: int | None = None
    module_id: int | None = None

    @model_validator(mode="after")
    def exactly_one_target(self) -> Self:
        if (self.course_id is None) == (self.module_id is None):
            raise ValueError("укажите ровно одно из полей: course_id или module_id")
        return self


class PurchaseGrant(PurchaseTarget):
    user_email: EmailStr
    payment_reference: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("user_email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class PurchaseRead(BaseModel):
    id: int
    user_id: int
    user_email: str
    course_id: int | None
    module_id: int | None
    course_title: str
    course_slug: str
    module_title: str | None
    purchased_at: datetime
    payment_reference: str
