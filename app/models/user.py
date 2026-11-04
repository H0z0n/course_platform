from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import ThemePreference, UserRole, db_enum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        db_enum(UserRole, "user_role"),
        default=UserRole.STUDENT,
        server_default=UserRole.STUDENT.value,
    )
    theme: Mapped[ThemePreference] = mapped_column(
        db_enum(ThemePreference, "theme_preference"),
        default=ThemePreference.LIGHT,
        server_default=ThemePreference.LIGHT.value,
    )
    personal_data_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
