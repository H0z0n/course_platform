from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ContentType, db_enum

if TYPE_CHECKING:
    from app.models.module import Module


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    content_type: Mapped[ContentType] = mapped_column(
        db_enum(ContentType, "content_type"),
        default=ContentType.TEXT,
        server_default=ContentType.TEXT.value,
    )
    content: Mapped[str] = mapped_column(Text, default="", server_default="")
    position: Mapped[int]
    duration_minutes: Mapped[int | None]
    is_free_preview: Mapped[bool] = mapped_column(default=False, server_default=false())

    module: Mapped["Module"] = relationship(back_populates="lessons", lazy="raise")
