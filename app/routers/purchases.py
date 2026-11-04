from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.dependencies import CurrentUser, SessionDep, StaffUser
from app.models import Purchase, User
from app.schemas.purchase import PurchaseGrant, PurchaseRead, PurchaseTarget
from app.services import mailer
from app.services.common import get_or_404
from app.services.emails import purchase_email
from app.services.site import get_site_settings
from app.services.purchases import (
    PURCHASE_LOAD_OPTIONS,
    create_purchase,
    new_payment_reference,
    to_purchase_read,
)

router = APIRouter(prefix="/purchases", tags=["purchases"])


async def notify_buyer(
    session: AsyncSession, background: BackgroundTasks, purchase: PurchaseRead
) -> PurchaseRead:
    site = await get_site_settings(session)
    background.add_task(mailer.deliver, purchase_email(purchase, site.site_name))
    return purchase


@router.post("/checkout", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
async def checkout(
    payload: PurchaseTarget, session: SessionDep, user: CurrentUser, background: BackgroundTasks
):
    if not settings.demo_payments:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Онлайн-оплата пока не подключена. Обратитесь к администратору.",
        )
    purchase = await create_purchase(
        session, user, payload, new_payment_reference("demo"), require_price=True
    )
    return await notify_buyer(session, background, to_purchase_read(purchase))


@router.get("/me", response_model=list[PurchaseRead])
async def my_purchases(session: SessionDep, user: CurrentUser):
    purchases = await session.scalars(
        select(Purchase)
        .where(Purchase.user_id == user.id)
        .options(*PURCHASE_LOAD_OPTIONS)
        .order_by(Purchase.purchased_at.desc(), Purchase.id.desc())
    )
    return [to_purchase_read(purchase) for purchase in purchases]


@router.get("", response_model=list[PurchaseRead])
async def list_purchases(
    session: SessionDep,
    _: StaffUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    purchases = await session.scalars(
        select(Purchase)
        .options(*PURCHASE_LOAD_OPTIONS)
        .order_by(Purchase.purchased_at.desc(), Purchase.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [to_purchase_read(purchase) for purchase in purchases]


@router.post("", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
async def grant_purchase(
    payload: PurchaseGrant, session: SessionDep, _: StaffUser, background: BackgroundTasks
):
    buyer = await session.scalar(select(User).where(User.email == payload.user_email))
    if buyer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь с таким email не найден")
    reference = payload.payment_reference or new_payment_reference("manual")
    purchase = await create_purchase(session, buyer, payload, reference, require_price=False)
    return await notify_buyer(session, background, to_purchase_read(purchase))


@router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_purchase(purchase_id: int, session: SessionDep, _: StaffUser):
    purchase = await get_or_404(session, Purchase, purchase_id, "Покупка не найдена")
    await session.delete(purchase)
    await session.commit()
