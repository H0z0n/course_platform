import pytest

SINGLE = {
    "kind": "single",
    "prompt": "Какой тип у значения 3.14?",
    "explanation": "Дробные числа — это float.",
    "options": [
        {"text": "int"},
        {"text": "float", "is_correct": True},
        {"text": "str"},
    ],
}
MULTIPLE = {
    "kind": "multiple",
    "prompt": "Какие имена допустимы?",
    "options": [
        {"text": "user_name", "is_correct": True},
        {"text": "2nd_place"},
        {"text": "_total", "is_correct": True},
    ],
}
TEXT = {
    "kind": "text",
    "prompt": "Что выведет print(type(True).__name__)?",
    "options": [{"text": "bool"}],
}


@pytest.fixture
def add_question(client, owner):
    async def factory(lesson, payload):
        response = await client.post(
            f"/api/lessons/{lesson.id}/questions", json=payload, headers=owner.headers
        )
        assert response.status_code == 201, response.text
        return response.json()

    return factory


def option_ids(question, *texts):
    return [option["id"] for option in question["options"] if option["text"] in texts]


async def answer(client, account, question_id, **body):
    return await client.post(
        f"/api/questions/{question_id}/answer", json=body, headers=account.headers
    )


async def test_question_validation(client, owner, tree):
    url = f"/api/lessons/{tree.free_lesson.id}/questions"
    two_correct = {**SINGLE, "options": [{"text": "a", "is_correct": True}, {"text": "b", "is_correct": True}]}
    none_correct = {**MULTIPLE, "options": [{"text": "a"}, {"text": "b"}]}
    one_option = {**SINGLE, "options": [{"text": "a", "is_correct": True}]}
    for payload in (two_correct, none_correct, one_option):
        assert (await client.post(url, json=payload, headers=owner.headers)).status_code == 422


async def test_students_cannot_manage_questions(client, student, tree):
    url = f"/api/lessons/{tree.free_lesson.id}/questions"
    assert (await client.post(url, json=SINGLE, headers=student.headers)).status_code == 403
    assert (await client.get(f"{url}/manage", headers=student.headers)).status_code == 403


async def test_public_questions_hide_correct_answers(client, tree, add_question):
    await add_question(tree.free_lesson, SINGLE)
    await add_question(tree.free_lesson, TEXT)
    questions = (await client.get(f"/api/lessons/{tree.free_lesson.id}/questions")).json()

    assert [question["kind"] for question in questions] == ["single", "text"]
    assert "is_correct" not in str(questions)
    assert questions[1]["options"] == []
    assert all(question["result"] is None for question in questions)


async def test_single_choice_grading(client, student, tree, add_question):
    question = await add_question(tree.free_lesson, SINGLE)

    wrong = await answer(client, student, question["id"], option_ids=option_ids(question, "int"))
    assert wrong.status_code == 200
    assert wrong.json()["is_correct"] is False
    assert wrong.json()["correct_option_ids"] == option_ids(question, "float")
    assert wrong.json()["explanation"] == "Дробные числа — это float."

    right = await answer(client, student, question["id"], option_ids=option_ids(question, "float"))
    assert right.json()["is_correct"] is True

    two = await answer(client, student, question["id"], option_ids=option_ids(question, "int", "str"))
    assert two.status_code == 422


async def test_multiple_choice_needs_exact_set(client, student, tree, add_question):
    question = await add_question(tree.free_lesson, MULTIPLE)
    partial = await answer(client, student, question["id"], option_ids=option_ids(question, "user_name"))
    exact = await answer(
        client, student, question["id"], option_ids=option_ids(question, "user_name", "_total")
    )
    assert partial.json()["is_correct"] is False
    assert exact.json()["is_correct"] is True


async def test_text_answer_ignores_case_and_spaces(client, student, tree, add_question):
    question = await add_question(tree.free_lesson, TEXT)
    right = await answer(client, student, question["id"], text="  BOOL ")
    wrong = await answer(client, student, question["id"], text="int")
    empty = await answer(client, student, question["id"], text="   ")
    assert right.json()["is_correct"] is True
    assert wrong.json()["is_correct"] is False
    assert wrong.json()["accepted_answers"] == ["bool"]
    assert empty.status_code == 422


async def test_foreign_option_is_rejected(client, student, tree, add_question):
    first = await add_question(tree.free_lesson, SINGLE)
    second = await add_question(tree.free_lesson, MULTIPLE)
    response = await answer(client, student, first["id"], option_ids=[second["options"][0]["id"]])
    assert response.status_code == 422


async def test_last_answer_is_remembered(client, student, tree, add_question):
    question = await add_question(tree.free_lesson, SINGLE)
    await answer(client, student, question["id"], option_ids=option_ids(question, "int"))
    await answer(client, student, question["id"], option_ids=option_ids(question, "float"))

    listed = (
        await client.get(f"/api/lessons/{tree.free_lesson.id}/questions", headers=student.headers)
    ).json()
    assert listed[0]["result"]["is_correct"] is True
    assert listed[0]["result"]["option_ids"] == option_ids(question, "float")


async def test_questions_of_locked_lesson_are_closed(client, student, tree, add_question):
    question = await add_question(tree.paid_lesson, SINGLE)
    url = f"/api/lessons/{tree.paid_lesson.id}/questions"
    assert (await client.get(url)).status_code == 401
    assert (await client.get(url, headers=student.headers)).status_code == 403
    blocked = await answer(client, student, question["id"], option_ids=option_ids(question, "float"))
    assert blocked.status_code == 403


async def test_editing_question_resets_answers(client, owner, student, tree, add_question):
    question = await add_question(tree.free_lesson, SINGLE)
    await answer(client, student, question["id"], option_ids=option_ids(question, "float"))

    edited = await client.put(f"/api/questions/{question['id']}", json=MULTIPLE, headers=owner.headers)
    assert edited.status_code == 200
    assert [option["text"] for option in edited.json()["options"]] == ["user_name", "2nd_place", "_total"]

    listed = (
        await client.get(f"/api/lessons/{tree.free_lesson.id}/questions", headers=student.headers)
    ).json()
    assert listed[0]["result"] is None


async def test_reorder_and_delete_questions(client, owner, tree, add_question):
    first = await add_question(tree.free_lesson, SINGLE)
    second = await add_question(tree.free_lesson, TEXT)
    url = f"/api/lessons/{tree.free_lesson.id}/questions"

    reordered = await client.put(
        f"{url}/order", json={"ids": [second["id"], first["id"]]}, headers=owner.headers
    )
    assert [question["id"] for question in reordered.json()] == [second["id"], first["id"]]

    assert (await client.delete(f"/api/questions/{second['id']}", headers=owner.headers)).status_code == 204
    remaining = (await client.get(f"{url}/manage", headers=owner.headers)).json()
    assert [question["id"] for question in remaining] == [first["id"]]


async def test_outline_counts_questions_and_shows_duration(client, owner, tree, add_question):
    await add_question(tree.free_lesson, SINGLE)
    await add_question(tree.free_lesson, TEXT)
    await client.patch(
        f"/api/lessons/{tree.free_lesson.id}", json={"duration_minutes": 15}, headers=owner.headers
    )

    outline = (await client.get("/api/courses/by-slug/python")).json()
    lesson = outline["modules"][0]["lessons"][0]
    assert (lesson["question_count"], lesson["duration_minutes"]) == (2, 15)


async def test_catalog_card_counts(client, owner, tree):
    await client.patch(
        f"/api/lessons/{tree.paid_lesson.id}", json={"duration_minutes": 20}, headers=owner.headers
    )
    await client.patch(
        f"/api/lessons/{tree.bundle_lesson.id}", json={"duration_minutes": 25}, headers=owner.headers
    )
    card = (await client.get("/api/courses")).json()[0]
    assert (
        card["module_count"],
        card["lesson_count"],
        card["free_lesson_count"],
        card["total_minutes"],
    ) == (2, 3, 1, 45)


async def test_course_cover_must_be_http_url(client, owner, tree):
    url = f"/api/courses/{tree.course.id}"
    bad = await client.patch(url, json={"cover_image_url": "javascript:alert(1)"}, headers=owner.headers)
    good = await client.patch(
        url, json={"cover_image_url": "https://example.com/cover.jpg"}, headers=owner.headers
    )
    cleared = await client.patch(url, json={"cover_image_url": None}, headers=owner.headers)
    assert bad.status_code == 422
    assert good.json()["cover_image_url"] == "https://example.com/cover.jpg"
    assert cleared.json()["cover_image_url"] is None
