async def test_start_complete_and_uncomplete(client, student, tree):
    url = f"/api/lessons/{tree.free_lesson.id}/progress"

    started = await client.post(f"{url}/start", headers=student.headers)
    assert started.status_code == 200
    assert started.json() == {
        "lesson_id": tree.free_lesson.id,
        "completed_at": None,
        "completed": False,
    }

    done = await client.put(url, json={"completed": True}, headers=student.headers)
    assert done.json()["completed"] is True

    started_again = await client.post(f"{url}/start", headers=student.headers)
    assert started_again.json()["completed"] is True

    undone = await client.put(url, json={"completed": False}, headers=student.headers)
    assert undone.json()["completed"] is False


async def test_completing_twice_keeps_first_timestamp(client, student, tree):
    url = f"/api/lessons/{tree.free_lesson.id}/progress"
    first = await client.put(url, json={"completed": True}, headers=student.headers)
    second = await client.put(url, json={"completed": True}, headers=student.headers)
    assert first.json()["completed_at"] == second.json()["completed_at"]


async def test_progress_requires_access_to_the_lesson(client, student, tree):
    url = f"/api/lessons/{tree.paid_lesson.id}/progress"
    assert (await client.put(url, json={"completed": True}, headers=student.headers)).status_code == 403
    assert (await client.post(f"{url}/start")).status_code == 401


async def test_course_progress_is_counted_on_the_fly(client, student, tree, buy):
    await buy(student.user, course=tree.course)
    for lesson in (tree.free_lesson, tree.paid_lesson):
        await client.put(
            f"/api/lessons/{lesson.id}/progress", json={"completed": True}, headers=student.headers
        )
    await client.post(f"/api/lessons/{tree.bundle_lesson.id}/progress/start", headers=student.headers)

    progress = (
        await client.get(f"/api/courses/{tree.course.id}/progress", headers=student.headers)
    ).json()
    assert (progress["total_lessons"], progress["completed_lessons"], progress["percent"]) == (
        3,
        2,
        66,
    )
    assert [lesson["completed"] for lesson in progress["lessons"]] == [True, True, False]


async def test_my_courses_lists_purchased_and_started(client, student, tree, other_course, buy):
    await buy(student.user, course=other_course)
    await client.put(
        f"/api/lessons/{tree.free_lesson.id}/progress",
        json={"completed": True},
        headers=student.headers,
    )

    courses = (await client.get("/api/progress/me", headers=student.headers)).json()
    summary = {
        course["slug"]: (course["has_purchase"], course["completed_lessons"], course["total_lessons"])
        for course in courses
    }
    assert summary == {"python": (False, 1, 3), "sql": (True, 0, 0)}


async def test_my_courses_is_empty_for_new_user(client, student):
    assert (await client.get("/api/progress/me", headers=student.headers)).json() == []
