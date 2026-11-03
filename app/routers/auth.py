from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.security import DUMMY_PASSWORD_HASH, create_access_token, hash_password, verify_password
from app.dependencies import CurrentUser, SessionDep, unauthorized
from app.models import User, UserRole
from app.schemas.user import PreferencesUpdate, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: SessionDep):
    existing_id = await session.scalar(select(User.id).where(User.email == payload.email))
    if existing_id is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь с таким email уже есть")
    user = User(
        email=payload.email,
        password_hash=await hash_password(payload.password),
        role=UserRole.STUDENT,
    )
    session.add(user)
    await session.commit()
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


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserRead)
async def update_preferences(payload: PreferencesUpdate, session: SessionDep, user: CurrentUser):
    user.theme = payload.theme
    await session.commit()
    return user
