import re

import pytest
from sqlalchemy import select

from app.core.security import create_password_reset_token
from app.models import User
from app.services import mailer

REGISTER = {"email": "new@example.com", "password": "secret123", "personal_data_consent": True}


@pytest.fixture
def outbox(monkeypatch):
    sent: list[mailer.Email] = []

    async def capture(email: mailer.Email) -> None:
        sent.append(email)

    monkeypatch.setattr(mailer, "deliver", capture)
    return sent


def reset_token(email: mailer.Email) -> str:
    match = re.search(r"token=(\S+)", email.text)
    assert match, email.text
    return match.group(1)


async def test_registration_requires_consent_and_records_it(client, session, outbox):
    without = await client.post("/api/auth/register", json={**REGISTER, "personal_data_consent": False})
    missing = await client.post(
        "/api/auth/register", json={"email": "new@example.com", "password": "secret123"}
    )
    assert without.status_code == missing.status_code == 422

    assert (await client.post("/api/auth/register", json=REGISTER)).status_code == 201
    user = await session.scalar(select(User).where(User.email == "new@example.com"))
    assert user.personal_data_consent_at is not None
    assert [email.to for email in outbox] == ["new@example.com"]


async def test_password_reset_flow(client, student, outbox):
    response = await client.post(
        "/api/auth/password-reset/request", json={"email": "Student@Example.com"}
    )
    assert response.status_code == 202
    assert len(outbox) == 1 and outbox[0].to == "student@example.com"
    token = reset_token(outbox[0])

    confirm = await client.post(
        "/api/auth/password-reset/confirm", json={"token": token, "password": "new-password-1"}
    )
    assert confirm.status_code == 204

    login = await client.post(
        "/api/auth/login", data={"username": "student@example.com", "password": "new-password-1"}
    )
    assert login.status_code == 200

    reused = await client.post(
        "/api/auth/password-reset/confirm", json={"token": token, "password": "another-pass-2"}
    )
    assert reused.status_code == 400


async def test_reset_request_does_not_reveal_unknown_email(client, student, outbox):
    known = await client.post("/api/auth/password-reset/request", json={"email": "student@example.com"})
    unknown = await client.post("/api/auth/password-reset/request", json={"email": "ghost@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert [email.to for email in outbox] == ["student@example.com"]


async def test_reset_and_access_tokens_are_not_interchangeable(client, student):
    reset = create_password_reset_token(student.user.id, student.user.password_hash)
    as_access = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {reset}"})
    assert as_access.status_code == 401

    access = student.headers["Authorization"].removeprefix("Bearer ")
    as_reset = await client.post(
        "/api/auth/password-reset/confirm", json={"token": access, "password": "new-password-1"}
    )
    assert as_reset.status_code == 400


async def test_buyer_gets_email_after_purchase(client, student, admin, tree, outbox):
    await client.post(
        "/api/purchases/checkout", json={"module_id": tree.paid_module.id}, headers=student.headers
    )
    await client.post(
        "/api/purchases",
        json={"user_email": "student@example.com", "module_id": tree.bundle_module.id},
        headers=admin.headers,
    )
    assert [email.to for email in outbox] == ["student@example.com", "student@example.com"]
    assert "Основы" in outbox[0].text
    assert "/courses/python" in outbox[0].text


async def test_legal_pages_have_templates_and_only_owner_edits(client, owner, admin):
    pages = (await client.get("/api/legal")).json()
    assert [page["slug"] for page in pages] == ["privacy", "consent"]
    assert all(page["is_template"] for page in pages)
    assert "152-ФЗ" in pages[0]["content"]

    body = {"title": "Политика", "content": "Текст политики"}
    assert (await client.put("/api/legal/privacy", json=body, headers=admin.headers)).status_code == 403
    updated = await client.put("/api/legal/privacy", json=body, headers=owner.headers)
    assert updated.status_code == 200
    assert updated.json()["is_template"] is False

    page = (await client.get("/api/legal/privacy")).json()
    assert (page["title"], page["content"]) == ("Политика", "Текст политики")
    assert (await client.get("/api/legal/unknown")).status_code == 422
