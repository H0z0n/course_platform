from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import create_access_token, password_hasher
from app.database import get_session
from app.main import app
from app.models import Base, ContentType, Course, Lesson, Module, Purchase, User, UserRole

DEV_DATABASE_URL = make_url(settings.database_url)
TEST_DATABASE_URL = DEV_DATABASE_URL.set(database=f"{DEV_DATABASE_URL.database}_test")
PASSWORD_HASH = password_hasher.hash("password123")


@dataclass
class Account:
    user: User
    headers: dict[str, str]


@dataclass
class CourseTree:
    course: Course
    paid_module: Module
    bundle_module: Module
    free_lesson: Lesson
    paid_lesson: Lesson
    bundle_lesson: Lesson


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


async def ensure_test_database_exists() -> None:
    server = create_async_engine(
        TEST_DATABASE_URL.set(database="postgres"), isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with server.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE_URL.database},
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE_URL.database}"'))
    await server.dispose()


@pytest.fixture(scope="session")
async def engine():
    await ensure_test_database_exists()
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_maker(engine):
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(session_maker):
    async with session_maker() as session:
        yield session


@pytest.fixture
async def client(session_maker, monkeypatch):
    monkeypatch.setattr(settings, "demo_payments", True)

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(session):
    async def factory(email: str, role: UserRole = UserRole.STUDENT) -> User:
        user = User(email=email, password_hash=PASSWORD_HASH, role=role)
        session.add(user)
        await session.commit()
        return user

    return factory


def as_account(user: User) -> Account:
    return Account(user=user, headers={"Authorization": f"Bearer {create_access_token(user.id)}"})


@pytest.fixture
async def owner(make_user) -> Account:
    return as_account(await make_user("owner@example.com", UserRole.OWNER))


@pytest.fixture
async def admin(make_user) -> Account:
    return as_account(await make_user("admin@example.com", UserRole.ADMIN))


@pytest.fixture
async def student(make_user) -> Account:
    return as_account(await make_user("student@example.com"))


@pytest.fixture
async def tree(session, owner) -> CourseTree:
    course = Course(
        title="Python", slug="python", price=Decimal("1000.00"), description="", owner_id=owner.user.id
    )
    paid_module = Module(course=course, title="Основы", position=1, price=Decimal("400.00"))
    bundle_module = Module(course=course, title="Продвинутое", position=2, price=None)
    free_lesson = Lesson(
        module=paid_module,
        title="Введение",
        position=1,
        is_free_preview=True,
        content_type=ContentType.TEXT,
        content="Привет!",
    )
    paid_lesson = Lesson(
        module=paid_module,
        title="Переменные",
        position=2,
        is_free_preview=False,
        content_type=ContentType.TEXT,
        content="x = 1",
    )
    bundle_lesson = Lesson(
        module=bundle_module,
        title="Декораторы",
        position=1,
        is_free_preview=False,
        content_type=ContentType.VIDEO,
        content="https://example.com/video.mp4",
    )
    session.add_all([course, paid_module, bundle_module, free_lesson, paid_lesson, bundle_lesson])
    await session.commit()
    return CourseTree(course, paid_module, bundle_module, free_lesson, paid_lesson, bundle_lesson)


@pytest.fixture
async def other_course(session, owner) -> Course:
    course = Course(
        title="SQL", slug="sql", price=Decimal("500.00"), description="", owner_id=owner.user.id
    )
    session.add(course)
    await session.commit()
    return course


@pytest.fixture
def buy(session):
    async def factory(
        user: User, *, course: Course | None = None, module: Module | None = None
    ) -> Purchase:
        purchase = Purchase(
            user_id=user.id,
            course_id=course.id if course else None,
            module_id=module.id if module else None,
            payment_reference=f"test_{uuid4().hex}",
        )
        session.add(purchase)
        await session.commit()
        return purchase

    return factory
