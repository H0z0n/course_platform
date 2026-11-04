from app.core.config import settings


async def test_defaults_before_any_change(client):
    site = (await client.get("/api/site")).json()
    assert site["site_name"] == settings.site_name
    assert site["hero_badge"] == "Первые уроки — бесплатно"
    assert site["hero_text"] is None
    assert site["accent_color"] is None
    assert site["logo_url"] is None


async def test_owner_rebrands_site(client, owner):
    response = await client.patch(
        "/api/site",
        json={
            "site_name": "  Школа Анны  ",
            "accent_color": "#C2410C",
            "logo_url": "https://example.com/logo.png",
            "hero_title": "Рисуем акварелью",
            "hero_text": "Курсы для начинающих художников.",
            "hero_badge": None,
        },
        headers=owner.headers,
    )
    assert response.status_code == 200
    site = (await client.get("/api/site")).json()
    assert site["site_name"] == "Школа Анны"
    assert site["accent_color"] == "#c2410c"
    assert site["hero_badge"] is None
    assert site["hero_title"] == "Рисуем акварелью"

    partial = await client.patch("/api/site", json={"hero_text": None}, headers=owner.headers)
    assert partial.json()["hero_text"] is None
    assert partial.json()["site_name"] == "Школа Анны"


async def test_only_owner_can_rebrand(client, admin, student):
    for account in (admin, student):
        response = await client.patch("/api/site", json={"site_name": "X"}, headers=account.headers)
        assert response.status_code == 403
    assert (await client.patch("/api/site", json={"site_name": "X"})).status_code == 401


async def test_site_settings_validation(client, owner):
    for payload in (
        {"accent_color": "red"},
        {"accent_color": "#12345"},
        {"logo_url": "javascript:alert(1)"},
        {"site_name": None},
        {"site_name": "   "},
        {"hero_title": None},
    ):
        response = await client.patch("/api/site", json=payload, headers=owner.headers)
        assert response.status_code == 422, payload
