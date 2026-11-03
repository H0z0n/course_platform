from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import OwnerUser, SessionDep, StaffUser
from app.models import User, UserRole
from app.schemas.user import RoleUpdate, UserRead
from app.services.common import get_or_404

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    session: SessionDep,
    _: StaffUser,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(User).order_by(User.id).limit(limit).offset(offset)
    if q:
        stmt = stmt.where(User.email.icontains(q.strip(), autoescape=True))
    return (await session.scalars(stmt)).all()


@router.patch("/{user_id}/role", response_model=UserRead)
async def change_role(user_id: int, payload: RoleUpdate, session: SessionDep, _: OwnerUser):
    if payload.role == UserRole.OWNER:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Роль owner назначается только скриптом create_owner"
        )
    user = await get_or_404(session, User, user_id, "Пользователь не найден")
    if user.role == UserRole.OWNER:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Роль владельца изменить нельзя")
    user.role = payload.role
    await session.commit()
    return user
