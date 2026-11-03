from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.module import Module


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )

    modules: Mapped[list["Module"]] = relationship(
        back_populates="course",
        order_by="Module.position, Module.id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
