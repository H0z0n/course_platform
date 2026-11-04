from enum import StrEnum

from sqlalchemy import Enum


class UserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    STUDENT = "student"


class ContentType(StrEnum):
    TEXT = "text"
    VIDEO = "video"


class ThemePreference(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class LegalSlug(StrEnum):
    PRIVACY = "privacy"
    CONSENT = "consent"


class QuestionKind(StrEnum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    TEXT = "text"


STAFF_ROLES =frozenset({UserRole.OWNER, UserRole.ADMIN})


def db_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda cls: [member.value for member in cls],
    )
