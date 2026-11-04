import hashlib
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_PURPOSE = "access"
RESET_PURPOSE = "password_reset"

password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash("dummy-password-for-equal-timing")


async def hash_password(password: str) -> str:
    return await run_in_threadpool(password_hasher.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    return await run_in_threadpool(password_hasher.verify, password, password_hash)


def encode_token(user_id: int, purpose: str, minutes: int, **extra: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=minutes)
    payload = {"sub": str(user_id), "purpose": purpose, "exp": expires_at, **extra}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, purpose: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    if payload.get("purpose") != purpose:
        return None
    return payload


def create_access_token(user_id: int) -> str:
    return encode_token(user_id, ACCESS_PURPOSE, settings.access_token_expire_minutes)


def decode_access_token(token: str) -> int | None:
    payload = decode_token(token, ACCESS_PURPOSE)
    try:
        return int(payload["sub"]) if payload else None
    except (KeyError, ValueError):
        return None


def password_fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def create_password_reset_token(user_id: int, password_hash: str) -> str:
    return encode_token(
        user_id,
        RESET_PURPOSE,
        settings.password_reset_expire_minutes,
        pwd=password_fingerprint(password_hash),
    )


def decode_password_reset_token(token: str) -> tuple[int, str] | None:
    payload = decode_token(token, RESET_PURPOSE)
    try:
        return (int(payload["sub"]), str(payload["pwd"])) if payload else None
    except (KeyError, ValueError):
        return None
