from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import SiteInfo

router = APIRouter(tags=["site"])


@router.get("/site", response_model=SiteInfo)
async def site_info():
    return SiteInfo(
        site_name=settings.site_name,
        currency=settings.currency,
        demo_payments=settings.demo_payments,
    )


@router.get("/health")
async def health():
    return {"status": "ok"}
