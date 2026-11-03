from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Course, Module, Purchase, User
from app.schemas.purchase import PurchaseRead, PurchaseTarget
from app.services.access import get_course_access
from app.services.common import get_or_404

PURCHASE_LOAD_OPTIONS = (
    selectinload(Purchase.user),
    selectinload(Purchase.course),
    selectinload(Purchase.module).selectinload(Module.course),
)


def new_payment_reference(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


async def create_purchase(
    session: AsyncSession,
    buyer: User,
    target: PurchaseTarget,
    payment_reference: str,
    require_price: bool,
) -> Purchase:
    if target.course_id is not None:
        course = await get_or_404(session, Course, target.course_id, "Курс не найден")
        if require_price and course.price is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Этот курс не продаётся целиком")
        access = await get_course_access(session, buyer, course.id)
        if access.course_purchased:
            raise HTTPException(status.HTTP_409_CONFLICT, "Курс уже куплен")
    else:
        module = await get_or_404(session, Module, target.module_id, "Модуль не найден")
        if require_price and module.price is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Этот модуль не продаётся отдельно")
        access = await get_course_access(session, buyer, module.course_id)
        if access.course_purchased:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Весь курс уже куплен — модуль и так доступен"
            )
        if module.id in access.purchased_module_ids:
            raise HTTPException(status.HTTP_409_CONFLICT, "Модуль уже куплен")

    reference_taken = await session.scalar(
        select(exists().where(Purchase.payment_reference == payment_reference))
    )
    if reference_taken:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Покупка с таким payment_reference уже есть"
        )

    purchase = Purchase(
        user_id=buyer.id,
        course_id=target.course_id,
        module_id=target.module_id,
        payment_reference=payment_reference,
    )
    session.add(purchase)
    await session.commit()
    return await load_purchase(session, purchase.id)


async def load_purchase(session: AsyncSession, purchase_id: int) -> Purchase:
    stmt = (
        select(Purchase)
        .where(Purchase.id == purchase_id)
        .options(*PURCHASE_LOAD_OPTIONS)
        .execution_options(populate_existing=True)
    )
    return (await session.scalars(stmt)).one()


def to_purchase_read(purchase: Purchase) -> PurchaseRead:
    course = purchase.course if purchase.course is not None else purchase.module.course
    return PurchaseRead(
        id=purchase.id,
        user_id=purchase.user_id,
        user_email=purchase.user.email,
        course_id=purchase.course_id,
        module_id=purchase.module_id,
        course_title=course.title,
        course_slug=course.slug,
        module_title=purchase.module.title if purchase.module is not None else None,
        purchased_at=purchase.purchased_at,
        payment_reference=purchase.payment_reference,
    )
