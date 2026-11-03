async def lesson_status(client, lesson, account=None) -> int:
    headers = account.headers if account else {}
    return (await client.get(f"/api/lessons/{lesson.id}", headers=headers)).status_code


async def test_anonymous_opens_only_free_preview(client, tree):
    assert await lesson_status(client, tree.free_lesson) == 200
    assert await lesson_status(client, tree.paid_lesson) == 401


async def test_student_without_purchase_gets_403(client, student, tree):
    assert await lesson_status(client, tree.free_lesson, student) == 200
    assert await lesson_status(client, tree.paid_lesson, student) == 403
    assert await lesson_status(client, tree.bundle_lesson, student) == 403


async def test_course_purchase_opens_every_lesson(client, student, tree, buy):
    await buy(student.user, course=tree.course)
    for lesson in (tree.free_lesson, tree.paid_lesson, tree.bundle_lesson):
        assert await lesson_status(client, lesson, student) == 200


async def test_module_purchase_opens_only_that_module(client, student, tree, buy):
    await buy(student.user, module=tree.paid_module)
    assert await lesson_status(client, tree.paid_lesson, student) == 200
    assert await lesson_status(client, tree.bundle_lesson, student) == 403


async def test_purchase_of_another_course_does_not_help(client, student, tree, other_course, buy):
    await buy(student.user, course=other_course)
    assert await lesson_status(client, tree.paid_lesson, student) == 403


async def test_purchase_of_another_user_does_not_help(client, student, make_user, tree, buy):
    friend = await make_user("friend@example.com")
    await buy(friend, course=tree.course)
    assert await lesson_status(client, tree.paid_lesson, student) == 403


async def test_staff_opens_everything(client, owner, admin, tree):
    for account in (owner, admin):
        for lesson in (tree.paid_lesson, tree.bundle_lesson):
            assert await lesson_status(client, lesson, account) == 200


async def test_lesson_response_contains_content(client, tree):
    lesson = (await client.get(f"/api/lessons/{tree.free_lesson.id}")).json()
    assert lesson["content"] == "Привет!"


async def test_outline_flags_follow_the_rule(client, student, tree, buy):
    await buy(student.user, module=tree.paid_module)
    outline = (
        await client.get(f"/api/courses/by-slug/{tree.course.slug}", headers=student.headers)
    ).json()

    assert outline["is_purchased"] is False
    purchased = {module["id"]: module["is_purchased"] for module in outline["modules"]}
    assert purchased == {tree.paid_module.id: True, tree.bundle_module.id: False}

    lessons = [lesson for module in outline["modules"] for lesson in module["lessons"]]
    assert {lesson["id"]: lesson["is_open"] for lesson in lessons} == {
        tree.free_lesson.id: True,
        tree.paid_lesson.id: True,
        tree.bundle_lesson.id: False,
    }
    assert all("content" not in lesson for lesson in lessons)


async def test_module_lessons_listing_uses_the_same_rule(client, tree):
    lessons = (await client.get(f"/api/modules/{tree.paid_module.id}/lessons")).json()
    assert [(lesson["id"], lesson["is_open"]) for lesson in lessons] == [
        (tree.free_lesson.id, True),
        (tree.paid_lesson.id, False),
    ]
