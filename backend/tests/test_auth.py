from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_login_and_me():
    email = "testuser@example.com"
    password = "CodeTest123!"

    register = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": email,
            "password": password,
        },
    )

    assert register.status_code == 201
    assert register.json()["email"] == email
    assert "password_hash" not in register.json()

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    me = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert me.status_code == 200
    assert me.json()["username"] == "testuser"


def test_invalid_login():
    response = client.post(
        "/auth/login",
        json={
            "email": "missing@example.com",
            "password": "Wrong123!",
        },
    )

    assert response.status_code == 401
