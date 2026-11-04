from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    password_fingerprint,
    verify_password,
)
from app.dependencies import CurrentUser, SessionDep, unauthorized
from app.models import User, UserRole
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    PreferencesUpdate,
    Token,
    UserCreate,
    UserRead,
)
from app.services import mailer
from app.services.emails import password_reset_email, welcome_email
from app.services.site import get_site_settings

router = APIRouter(prefix="/auth", tags=["auth"])

RESET_REQUESTED = "Если такой email зарегистрирован, мы отправили на него ссылку для восстановления пароля"


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: SessionDep, background: BackgroundTasks):
    existing_id = await session.scalar(select(User.id).where(User.email == payload.email))
    if existing_id is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь с таким email уже есть")
    user = User(
        email=payload.email,
        password_hash=await hash_password(payload.password),
        role=UserRole.STUDENT,
        personal_data_consent_at=datetime.now(UTC),
    )
    session.add(user)
    await session.commit()
    site = await get_site_settings(session)
    background.add_task(mailer.deliver, welcome_email(user.email, site.site_name))
    return user


@router.post("/login", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    email = form.username.strip().lower()
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        await verify_password(form.password, DUMMY_PASSWORD_HASH)
        raise unauthorized("Неверный email или пароль")
    if not await verify_password(form.password, user.password_hash):
        raise unauthorized("Неверный email или пароль")
    return Token(access_token=create_access_token(user.id))


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    payload: PasswordResetRequest, session: SessionDep, background: BackgroundTasks
):
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user is not None:
        site = await get_site_settings(session)
        token = create_password_reset_token(user.id, user.password_hash)
        background.add_task(mailer.deliver, password_reset_email(user.email, site.site_name, token))
    return {"detail": RESET_REQUESTED}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(payload: PasswordResetConfirm, session: SessionDep):
    decoded = decode_password_reset_token(payload.token)
    user = await session.get(User, decoded[0]) if decoded else None
    if user is None or password_fingerprint(user.password_hash) != decoded[1]:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Ссылка недействительна или уже использована. Запросите восстановление ещё раз.",
        )
    user.password_hash = await hash_password(payload.password)
    await session.commit()


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserRead)
async def update_preferences(payload: PreferencesUpdate, session: SessionDep, user: CurrentUser):
    user.theme = payload.theme
    await session.commit()
    return user
