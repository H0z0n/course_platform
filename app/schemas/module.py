from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Money, PatchModel, Position, Title


class ModuleCreate(BaseModel):
    title: Title
    price: Money | None = None
    position: Position | None = None


class ModuleUpdate(PatchModel):
    nullable_fields = frozenset({"price"})

    title: Title | None = None
    price: Money | None = None
    position: Position | None = None


class ModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    position: int
    price: Decimal | None
