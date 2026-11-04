from sqlalchemy import func, select

from app.models import LessonProgress


async def test_site_info_and_health(client):
    site = await client.get("/api/site")
    assert site.status_code == 200
    assert {"site_name", "currency", "demo_payments", "hero_title"} <= set(site.json())
    assert (await client.get("/api/health")).json() == {"status": "ok"}


async def test_owner_builds_course_with_auto_positions(client, owner):
    course = await client.post(
        "/api/courses",
        json={"title": "  Python  ", "slug": "python", "price": "1990"},
        headers=owner.headers,
    )
    assert course.status_code == 201
    assert course.json()["title"] == "Python"
    assert course.json()["price"] == "1990.00"
    assert course.json()["owner_id"] == owner.user.id
    course_id = course.json()["id"]

    first = await client.post(
        f"/api/courses/{course_id}/modules", json={"title": "Основы"}, headers=owner.headers
    )
    second = await client.post(
        f"/api/courses/{course_id}/modules",
        json={"title": "Функции", "price": "500"},
        headers=owner.headers,
    )
    assert (first.json()["position"], second.json()["position"]) == (1, 2)
    assert first.json()["price"] is None

    lesson = await client.post(
        f"/api/modules/{first.json()['id']}/lessons",
        json={"title": "Привет", "content": "# Заголовок"},
        headers=owner.headers,
    )
    assert lesson.status_code == 201
    assert lesson.json()["position"] == 1
    assert lesson.json()["content_type"] == "text"
    assert lesson.json()["is_free_preview"] is False


async def test_slug_must_be_unique_and_valid(client, owner, tree):
    duplicate = await client.post(
        "/api/courses", json={"title": "Другой", "slug": "python"}, headers=owner.headers
    )
    invalid = await client.post(
        "/api/courses", json={"title": "Другой", "slug": "Не Slug"}, headers=owner.headers
    )
    assert duplicate.status_code == 409
    assert invalid.status_code == 422


async def test_patch_changes_only_sent_fields(client, owner, tree):
    url = f"/api/courses/{tree.course.id}"
    response = await client.patch(url, json={"price": None}, headers=owner.headers)
    assert response.status_code == 200
    assert response.json()["price"] is None
    assert response.json()["title"] == "Python"

    clear_title = await client.patch(url, json={"title": None}, headers=owner.headers)
    assert clear_title.status_code == 422


async def test_reorder_modules(client, owner, tree):
    url = f"/api/courses/{tree.course.id}/modules/order"
    new_order = [tree.bundle_module.id, tree.paid_module.id]
    response = await client.put(url, json={"ids": new_order}, headers=owner.headers)
    assert [module["id"] for module in response.json()] == new_order

    outline = (await client.get(f"/api/courses/{tree.course.id}")).json()
    assert [module["id"] for module in outline["modules"]] == new_order

    incomplete = await client.put(url, json={"ids": [tree.paid_module.id]}, headers=owner.headers)
    repeated = await client.put(
        url, json={"ids": [tree.paid_module.id, tree.paid_module.id]}, headers=owner.headers
    )
    assert incomplete.status_code == repeated.status_code == 400


async def test_reorder_lessons(client, owner, tree):
    new_order = [tree.paid_lesson.id, tree.free_lesson.id]
    response = await client.put(
        f"/api/modules/{tree.paid_module.id}/lessons/order",
        json={"ids": new_order},
        headers=owner.headers,
    )
    assert [(lesson["id"], lesson["position"]) for lesson in response.json()] == [
        (tree.paid_lesson.id, 1),
        (tree.free_lesson.id, 2),
    ]


async def test_outline_is_sorted_by_position(client, owner, tree):
    await client.patch(
        f"/api/lessons/{tree.free_lesson.id}", json={"position": 5}, headers=owner.headers
    )
    outline = (await client.get("/api/courses/by-slug/python")).json()
    assert [lesson["id"] for lesson in outline["modules"][0]["lessons"]] == [
        tree.paid_lesson.id,
        tree.free_lesson.id,
    ]


async def test_video_lesson_requires_http_url(client, owner, tree):
    created = await client.post(
        f"/api/modules/{tree.paid_module.id}/lessons",
        json={"title": "Видео", "content_type": "video", "content": "javascript:alert(1)"},
        headers=owner.headers,
    )
    assert created.status_code == 422

    url = f"/api/lessons/{tree.paid_lesson.id}"
    only_type = await client.patch(url, json={"content_type": "video"}, headers=owner.headers)
    assert only_type.status_code == 422

    with_link = await client.patch(
        url,
        json={"content_type": "video", "content": "https://youtu.be/abc"},
        headers=owner.headers,
    )
    assert with_link.status_code == 200


async def test_move_lesson_to_another_module_puts_it_last(client, owner, tree):
    response = await client.patch(
        f"/api/lessons/{tree.free_lesson.id}",
        json={"module_id": tree.bundle_module.id},
        headers=owner.headers,
    )
    assert response.status_code == 200
    assert response.json()["module_id"] == tree.bundle_module.id
    assert response.json()["position"] == 2


async def test_delete_course_removes_modules_lessons_and_progress(
    client, session, owner, student, tree
):
    session.add(LessonProgress(user_id=student.user.id, lesson_id=tree.free_lesson.id))
    await session.commit()

    response = await client.delete(f"/api/courses/{tree.course.id}", headers=owner.headers)
    assert response.status_code == 204
    assert (await client.get(f"/api/courses/{tree.course.id}")).status_code == 404
    assert (await client.get(f"/api/modules/{tree.paid_module.id}")).status_code == 404
    assert (await client.get(f"/api/lessons/{tree.free_lesson.id}")).status_code == 404
    assert await session.scalar(select(func.count()).select_from(LessonProgress)) == 0


async def test_purchased_content_cannot_be_deleted(client, owner, student, tree, buy):
    await buy(student.user, module=tree.paid_module)
    course = await client.delete(f"/api/courses/{tree.course.id}", headers=owner.headers)
    module = await client.delete(f"/api/modules/{tree.paid_module.id}", headers=owner.headers)
    other_module = await client.delete(
        f"/api/modules/{tree.bundle_module.id}", headers=owner.headers
    )
    assert course.status_code == module.status_code == 409
    assert other_module.status_code == 204


async def test_unknown_ids_give_404(client, owner):
    assert (await client.get("/api/courses/999")).status_code == 404
    assert (await client.get("/api/courses/by-slug/nope")).status_code == 404
    assert (await client.get("/api/lessons/999")).status_code == 404
    patch = await client.patch("/api/modules/999", json={"title": "X"}, headers=owner.headers)
    assert patch.status_code == 404
