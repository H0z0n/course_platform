from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.module import Module
    from app.models.user import User


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint(
            "(course_id IS NOT NULL AND module_id IS NULL)"
            " OR (course_id IS NULL AND module_id IS NOT NULL)",
            name="exactly_one_target",
        ),
        UniqueConstraint("user_id", "course_id"),
        UniqueConstraint("user_id", "module_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), index=True
    )
    module_id: Mapped[int | None] = mapped_column(
        ForeignKey("modules.id", ondelete="RESTRICT"), index=True
    )
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    payment_reference: Mapped[str] = mapped_column(String(255), unique=True)

    user: Mapped["User"] = relationship(lazy="raise")
    course: Mapped["Course | None"] = relationship(lazy="raise")
    module: Mapped["Module | None"] = relationship(lazy="raise")
