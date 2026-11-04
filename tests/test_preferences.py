async def test_new_user_gets_light_theme(client):
    registered = await client.post(
        "/api/auth/register",
        json={"email": "new@example.com", "password": "secret123", "personal_data_consent": True},
    )
    assert registered.json()["theme"] == "light"


async def test_theme_is_saved_to_account(client, student):
    for theme in ("dark", "system"):
        response = await client.patch("/api/auth/me", json={"theme": theme}, headers=student.headers)
        assert response.status_code == 200
        assert response.json()["theme"] == theme
    me = await client.get("/api/auth/me", headers=student.headers)
    assert me.json()["theme"] == "system"


async def test_theme_validation_and_auth(client, student):
    bad = await client.patch("/api/auth/me", json={"theme": "pink"}, headers=student.headers)
    anonymous = await client.patch("/api/auth/me", json={"theme": "dark"})
    assert bad.status_code == 422
    assert anonymous.status_code == 401


async def test_catalog_card_counts_questions(client, owner, tree):
    assert (await client.get("/api/courses")).json()[0]["question_count"] == 0
    await client.post(
        f"/api/lessons/{tree.free_lesson.id}/questions",
        json={"kind": "text", "prompt": "2 + 2?", "options": [{"text": "4"}]},
        headers=owner.headers,
    )
    assert (await client.get("/api/courses")).json()[0]["question_count"] == 1
