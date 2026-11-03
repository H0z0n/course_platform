import argparse
import asyncio
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.database import async_session_maker, engine
from app.models import User, UserRole


async def create_owner(email: str, password: str | None = None) -> str:
    async with async_session_maker() as session:
        existing_owner = await session.scalar(select(User).where(User.role == UserRole.OWNER))
        if existing_owner is not None:
            return f"Владелец уже есть: {existing_owner.email}. Второй не создаётся."

        user = await session.scalar(select(User).where(User.email == email))
        if user is not None:
            user.role = UserRole.OWNER
            await session.commit()
            return f"Пользователь {email} назначен владельцем (пароль не изменён)."

        if password is None:
            password = ask_password()
        session.add(
            User(email=email, password_hash=await hash_password(password), role=UserRole.OWNER)
        )
        await session.commit()
        return f"Владелец {email} создан."


def ask_password() -> str:
    password = getpass.getpass("Пароль владельца: ")
    if len(password) < 8:
        raise SystemExit("Пароль должен быть не короче 8 символов.")
    if password != getpass.getpass("Повторите пароль: "):
        raise SystemExit("Пароли не совпадают.")
    return password


async def run(email: str) -> None:
    try:
        print(await create_owner(email))
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Создать владельца (owner) платформы.")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.email.strip().lower()))


if __name__ == "__main__":
    main()
