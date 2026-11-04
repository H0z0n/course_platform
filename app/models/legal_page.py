from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import LegalSlug, db_enum


class LegalPage(Base):
    __tablename__ = "legal_pages"

    slug: Mapped[LegalSlug] = mapped_column(db_enum(LegalSlug, "legal_slug"), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
