from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SiteSettings(Base):
    __tablename__ = "site_settings"
    __table_args__ = (CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    site_name: Mapped[str] = mapped_column(String(100))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    accent_color: Mapped[str | None] = mapped_column(String(7))
    hero_badge: Mapped[str | None] = mapped_column(String(100))
    hero_title: Mapped[str] = mapped_column(String(200))
    hero_text: Mapped[str | None] = mapped_column(String(500))
