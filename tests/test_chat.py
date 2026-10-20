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


def test_chat_requires_login():
    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "你好"}]},
    )
    assert response.status_code == 401


def test_screen_command_is_returned(monkeypatch):
    calls = {"n": 0}

    def fake_complete(messages):
        assert messages[0]["role"] == "system"
        assert "只能使用本次请求提供的工具" in messages[0]["content"]
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "selectBuilding",
                            "arguments": '{"building": "5"}',
                        },
                    }
                ],
            }
        return {"role": "assistant", "content": "已记下，定位到5号馆"}

#monkeypatch 会把 complete 换成假函数，所以测试不会访问外网。
    monkeypatch.setattr("app.ai_chat.complete", fake_complete)
    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "切到5号馆"}]},
        headers=headers(),
    )
    data = response.json()["data"]
    assert response.status_code == 200
    assert data["reply"] == "已记下，定位到5号馆"
    assert data["commands"][0]["params"]["building"] == "5号馆"
    assert data["commands"][0]["kind"] == "screen"