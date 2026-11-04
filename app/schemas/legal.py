from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models import LegalSlug


class LegalPageRead(BaseModel):
    slug: LegalSlug
    title: str
    content: str
    updated_at: datetime | None
    is_template: bool


class LegalPageUpdate(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100_000)]
