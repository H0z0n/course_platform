from app.core.config import settings
from app.core.security import create_access_token


async def test_register_login_and_me(client):
    registered = await client.post(
        "/api/auth/register", json={"email": "New@Example.com", "password": "secret123"}
    )
    assert registered.status_code == 201
    assert registered.json()["email"] == "new@example.com"
    assert registered.json()["role"] == "student"
    assert "password_hash" not in registered.json()

    login = await client.post(
        "/api/auth/login", data={"username": "NEW@example.com", "password": "secret123"}
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"

    me = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "new@example.com"


async def test_register_rejects_duplicate_email_in_any_case(client, student):
    response = await client.post(
        "/api/auth/register", json={"email": "STUDENT@example.com", "password": "secret123"}
    )
    assert response.status_code == 409


async def test_register_validates_input(client):
    response = await client.post(
        "/api/auth/register", json={"email": "not-an-email", "password": "short"}
    )
    assert response.status_code == 422


async def test_wrong_password_and_unknown_email_look_the_same(client, student):
    wrong_password = await client.post(
        "/api/auth/login", data={"username": "student@example.com", "password": "wrong-one"}
    )
    unknown_email = await client.post(
        "/api/auth/login", data={"username": "nobody@example.com", "password": "password123"}
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


async def test_me_requires_token(client):
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_bad_token_is_rejected_even_on_public_endpoint(client, tree):
    bad = {"Authorization": "Bearer garbage"}
    assert (await client.get("/api/courses/by-slug/python", headers=bad)).status_code == 401
    assert (await client.get(f"/api/lessons/{tree.free_lesson.id}", headers=bad)).status_code == 401
    assert (await client.get("/api/courses/by-slug/python")).status_code == 200


async def test_expired_token_is_rejected(client, student, monkeypatch):
    monkeypatch.setattr(settings, "access_token_expire_minutes", -1)
    expired = create_access_token(student.user.id)
    response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


async def test_student_cannot_manage_content(client, student):
    response = await client.post(
        "/api/courses", json={"title": "X", "slug": "x"}, headers=student.headers
    )
    assert response.status_code == 403


async def test_only_owner_changes_roles(client, owner, admin, student):
    promote = await client.patch(
        f"/api/users/{student.user.id}/role", json={"role": "admin"}, headers=owner.headers
    )
    assert promote.status_code == 200
    assert promote.json()["role"] == "admin"

    by_admin = await client.patch(
        f"/api/users/{student.user.id}/role", json={"role": "student"}, headers=admin.headers
    )
    make_owner = await client.patch(
        f"/api/users/{student.user.id}/role", json={"role": "owner"}, headers=owner.headers
    )
    demote_owner = await client.patch(
        f"/api/users/{owner.user.id}/role", json={"role": "admin"}, headers=owner.headers
    )
    assert by_admin.status_code == 403
    assert make_owner.status_code == 400
    assert demote_owner.status_code == 400


async def test_staff_lists_users_with_search(client, admin, student):
    response = await client.get("/api/users", params={"q": "STUD"}, headers=admin.headers)
    assert response.status_code == 200
    assert [user["email"] for user in response.json()] == ["student@example.com"]
