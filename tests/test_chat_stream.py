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


def test_stream_requires_login():
    response = client.post(
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "你好"}]},
    )
    assert response.status_code == 401


def test_stream_deltas(monkeypatch):
    def fake_stream(messages):
        yield {"choices": [{"delta": {"content": "已"}, "finish_reason": None}]}
        yield {"choices": [{"delta": {"content": "记下"}, "finish_reason": "stop"}]}

    monkeypatch.setattr("app.ai_chat.complete_stream", fake_stream)
    response = client.post(
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "切到5号馆"}]},
        headers=headers(),
    )
    assert response.status_code == 200
    assert "event: delta" in response.text
    assert "已" in response.text
    assert "记下" in response.text
    assert "event: done" in response.text