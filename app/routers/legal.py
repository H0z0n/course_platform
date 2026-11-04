from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import OwnerUser, SessionDep
from app.models import LegalPage, LegalSlug
from app.schemas.legal import LegalPageRead, LegalPageUpdate
from app.services.legal import DEFAULT_LEGAL_PAGES

router = APIRouter(prefix="/legal", tags=["legal"])


async def read_page(session: AsyncSession, slug: LegalSlug) -> LegalPageRead:
    page = await session.get(LegalPage, slug)
    if page is None:
        title, content = DEFAULT_LEGAL_PAGES[slug]
        return LegalPageRead(slug=slug, title=title, content=content, updated_at=None, is_template=True)
    return LegalPageRead(
        slug=slug,
        title=page.title,
        content=page.content,
        updated_at=page.updated_at,
        is_template=False,
    )


@router.get("", response_model=list[LegalPageRead])
async def list_pages(session: SessionDep):
    return [await read_page(session, slug) for slug in LegalSlug]


@router.get("/{slug}", response_model=LegalPageRead)
async def get_page(slug: LegalSlug, session: SessionDep):
    return await read_page(session, slug)


@router.put("/{slug}", response_model=LegalPageRead)
async def update_page(slug: LegalSlug, payload: LegalPageUpdate, session: SessionDep, _: OwnerUser):
    page = await session.get(LegalPage, slug)
    if page is None:
        page = LegalPage(slug=slug)
        session.add(page)
    page.title = payload.title
    page.content = payload.content
    page.updated_at = datetime.now(UTC)
    await session.commit()
    return await read_page(session, slug)
