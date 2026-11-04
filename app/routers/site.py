from fastapi import APIRouter

from app.dependencies import OwnerUser, SessionDep
from app.models import SiteSettings
from app.schemas.common import SiteInfo, SiteSettingsUpdate
from app.services.site import SETTINGS_ROW_ID, default_site_settings, get_site_settings, to_site_info

router = APIRouter(tags=["site"])


@router.get("/site", response_model=SiteInfo)
async def site_info(session: SessionDep):
    return to_site_info(await get_site_settings(session))


@router.patch("/site", response_model=SiteInfo)
async def update_site(payload: SiteSettingsUpdate, session: SessionDep, _: OwnerUser):
    site = await session.get(SiteSettings, SETTINGS_ROW_ID)
    if site is None:
        site = default_site_settings()
        session.add(site)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(site, field, value)
    await session.commit()
    return to_site_info(site)


@router.get("/health")
async def health():
    return {"status": "ok"}
