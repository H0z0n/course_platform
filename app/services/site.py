from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import SiteSettings
from app.schemas.common import SiteInfo

SETTINGS_ROW_ID = 1


def default_site_settings() -> SiteSettings:
    return SiteSettings(
        id=SETTINGS_ROW_ID,
        site_name=settings.site_name,
        logo_url=None,
        accent_color=None,
        hero_badge="Первые уроки — бесплатно",
        hero_title="Учитесь в своём темпе —\nглава за главой",
        hero_text=None,
    )


async def get_site_settings(session: AsyncSession) -> SiteSettings:
    return await session.get(SiteSettings, SETTINGS_ROW_ID) or default_site_settings()


def to_site_info(site: SiteSettings) -> SiteInfo:
    return SiteInfo(
        site_name=site.site_name,
        logo_url=site.logo_url,
        accent_color=site.accent_color,
        hero_badge=site.hero_badge,
        hero_title=site.hero_title,
        hero_text=site.hero_text,
        currency=settings.currency,
        demo_payments=settings.demo_payments,
    )
