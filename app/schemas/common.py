from decimal import Decimal
from typing import Annotated, ClassVar
from urllib.parse import urlparse

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    StringConstraints,
    ValidationInfo,
    field_validator,
)

from app.models import ContentType

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
CENT = Decimal("0.01")


def round_to_cents(value: Decimal) -> Decimal:
    return value.quantize(CENT)


def is_http_url(value: str) -> bool:
    url = urlparse(value)
    return url.scheme in ("http", "https") and bool(url.netloc)


def check_http_url(value: str) -> str:
    if not is_http_url(value):
        raise ValueError("нужна ссылка, начинающаяся с http:// или https://")
    return value


HttpUrlText = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=500), AfterValidator(check_http_url)
]
Minutes = Annotated[int, Field(ge=1, le=1000)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Slug = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100, pattern=SLUG_PATTERN)]
Money = Annotated[
    Decimal, Field(ge=0, max_digits=10, decimal_places=2), AfterValidator(round_to_cents)
]
Position = Annotated[int, Field(ge=1)]


class PatchModel(BaseModel):
    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @field_validator("*")
    @classmethod
    def reject_null(cls, value: object, info: ValidationInfo) -> object:
        if value is None and info.field_name not in cls.nullable_fields:
            raise ValueError("это поле нельзя очистить")
        return value


def validate_lesson_content(content_type: ContentType, content: str) -> None:
    if content_type != ContentType.VIDEO or not content:
        return
    if not is_http_url(content):
        raise ValueError("для видео-урока content должен быть ссылкой http:// или https://")


class ReorderRequest(BaseModel):
    ids: list[int]


HexColor = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^#[0-9a-fA-F]{6}$")
]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class SiteInfo(BaseModel):
    site_name: str
    logo_url: str | None
    accent_color: str | None
    hero_badge: str | None
    hero_title: str
    hero_text: str | None
    currency: str
    demo_payments: bool


class SiteSettingsUpdate(PatchModel):
    nullable_fields = frozenset({"logo_url", "accent_color", "hero_badge", "hero_text"})

    site_name: ShortText | None = None
    logo_url: HttpUrlText | None = None
    accent_color: HexColor | None = None
    hero_badge: ShortText | None = None
    hero_title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)] | None = None
    hero_text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)] | None = None
