from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

ALGORITHM = "HS256"

password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash("dummy-password-for-equal-timing")


async def hash_password(password: str) -> str:
    return await run_in_threadpool(password_hasher.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    return await run_in_threadpool(password_hasher.verify, password, password_hash)


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
