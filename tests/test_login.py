from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_wrong_password_returns_401():
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == 401
    assert body["data"] is None
    assert "密码" in body["msg"]
