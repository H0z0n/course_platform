import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models import Purchase


async def checkout(client, account, **target):
    return await client.post("/api/purchases/checkout", json=target, headers=account.headers)


async def test_checkout_course_opens_lessons(client, student, tree):
    response = await checkout(client, student, course_id=tree.course.id)
    assert response.status_code == 201
    body = response.json()
    assert (body["course_title"], body["module_id"], body["user_email"]) == (
        "Python",
        None,
        "student@example.com",
    )
    assert body["payment_reference"].startswith("demo_")

    lesson = await client.get(f"/api/lessons/{tree.bundle_lesson.id}", headers=student.headers)
    assert lesson.status_code == 200


async def test_checkout_module(client, student, tree):
    response = await checkout(client, student, module_id=tree.paid_module.id)
    assert response.status_code == 201
    assert response.json()["module_title"] == "Основы"
    assert response.json()["course_slug"] == "python"


async def test_checkout_requires_a_price(client, owner, student, tree):
    assert (await checkout(client, student, module_id=tree.bundle_module.id)).status_code == 400

    await client.patch(f"/api/courses/{tree.course.id}", json={"price": None}, headers=owner.headers)
    assert (await checkout(client, student, course_id=tree.course.id)).status_code == 400


async def test_duplicate_and_redundant_purchases_are_rejected(client, student, tree):
    assert (await checkout(client, student, module_id=tree.paid_module.id)).status_code == 201
    assert (await checkout(client, student, module_id=tree.paid_module.id)).status_code == 409
    assert (await checkout(client, student, course_id=tree.course.id)).status_code == 201
    assert (await checkout(client, student, course_id=tree.course.id)).status_code == 409
    assert (await checkout(client, student, module_id=tree.paid_module.id)).status_code == 409


async def test_checkout_needs_exactly_one_target(client, student, tree):
    assert (await checkout(client, student)).status_code == 422
    both = await checkout(client, student, course_id=tree.course.id, module_id=tree.paid_module.id)
    assert both.status_code == 422


async def test_checkout_is_off_without_demo_mode(client, student, tree, monkeypatch):
    monkeypatch.setattr(settings, "demo_payments", False)
    assert (await checkout(client, student, course_id=tree.course.id)).status_code == 503


async def test_checkout_requires_login(client, tree):
    response = await client.post("/api/purchases/checkout", json={"course_id": tree.course.id})
    assert response.status_code == 401


async def test_staff_grants_and_revokes_access(client, admin, student, tree):
    grant = await client.post(
        "/api/purchases",
        json={"user_email": "Student@Example.com", "module_id": tree.bundle_module.id},
        headers=admin.headers,
    )
    assert grant.status_code == 201
    assert grant.json()["payment_reference"].startswith("manual_")
    lesson_url = f"/api/lessons/{tree.bundle_lesson.id}"
    assert (await client.get(lesson_url, headers=student.headers)).status_code == 200

    listing = await client.get("/api/purchases", headers=admin.headers)
    assert [purchase["user_email"] for purchase in listing.json()] == ["student@example.com"]

    revoke = await client.delete(f"/api/purchases/{grant.json()['id']}", headers=admin.headers)
    assert revoke.status_code == 204
    assert (await client.get(lesson_url, headers=student.headers)).status_code == 403


async def test_grant_checks_user_and_payment_reference(client, admin, student, tree):
    unknown = await client.post(
        "/api/purchases",
        json={"user_email": "ghost@example.com", "course_id": tree.course.id},
        headers=admin.headers,
    )
    assert unknown.status_code == 404

    first = await client.post(
        "/api/purchases",
        json={
            "user_email": "student@example.com",
            "module_id": tree.paid_module.id,
            "payment_reference": "INV-1",
        },
        headers=admin.headers,
    )
    same_reference = await client.post(
        "/api/purchases",
        json={
            "user_email": "student@example.com",
            "module_id": tree.bundle_module.id,
            "payment_reference": "INV-1",
        },
        headers=admin.headers,
    )
    assert first.status_code == 201
    assert same_reference.status_code == 409


async def test_students_cannot_use_staff_endpoints(client, student, tree):
    assert (await client.get("/api/purchases", headers=student.headers)).status_code == 403
    grant = await client.post(
        "/api/purchases",
        json={"user_email": "student@example.com", "course_id": tree.course.id},
        headers=student.headers,
    )
    assert grant.status_code == 403


async def test_my_purchases(client, student, tree, buy):
    await buy(student.user, module=tree.paid_module)
    purchases = (await client.get("/api/purchases/me", headers=student.headers)).json()
    assert [(p["course_title"], p["module_title"]) for p in purchases] == [("Python", "Основы")]


async def test_database_rejects_purchase_with_both_targets(session, student, tree):
    session.add(
        Purchase(
            user_id=student.user.id,
            course_id=tree.course.id,
            module_id=tree.paid_module.id,
            payment_reference="both",
        )
    )
    with pytest.raises(IntegrityError, match="ck_purchases_exactly_one_target"):
        await session.commit()


async def test_database_rejects_purchase_without_target(session, student):
    session.add(Purchase(user_id=student.user.id, payment_reference="none"))
    with pytest.raises(IntegrityError, match="ck_purchases_exactly_one_target"):
        await session.commit()
