from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def headers():
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_roam_is_rejected():
    response = client.post(
        "/api/scene/command",
        json={"action": "startRoam", "params": {"route": "route1"}},
        headers=headers(),
    )
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["ok"] is False
    assert "不支持" in body["data"]["results"][0]["message"]


def test_building_alias_is_normalized():
    response = client.post(
        "/api/scene/command",
        json={"action": "selectBuilding", "params": {"building": "5"}},
        headers=headers(),
    )
    result = response.json()["data"]["results"][0]
    assert result["ok"] is True
    assert result["kind"] == "screen"
    assert result["params"]["building"] == "5号馆"


def test_query_hall():
    response = client.post(
        "/api/scene/command",
        json={"action": "queryHall", "params": {"name": "1号馆"}},
        headers=headers(),
    )
    result = response.json()["data"]["results"][0]
    assert result["ok"] is True
    assert result["data"]["name"] == "1号馆"
    assert result["data"]["area_sqm"] > 0


def test_command_requires_login():
    response = client.post(
        "/api/scene/command",
        json={"action": "overview", "params": {}},
    )
    assert response.status_code == 401