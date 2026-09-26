from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_user(username: str, email: str):
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "CodeTest123!",
        },
    )
    assert response.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "CodeTest123!",
        },
    )
    assert login.status_code == 200

    return login.json()["access_token"]


def auth(token: str):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_project(token: str):
    workspace = client.post(
        "/workspaces",
        json={
            "name": "Version History Workspace",
        },
        headers=auth(token),
    )

    assert workspace.status_code == 201

    workspace_id = workspace.json()["id"]

    project = client.post(
        f"/workspaces/{workspace_id}/projects",
        json={
            "name": "Version History Project",
        },
        headers=auth(token),
    )

    assert project.status_code == 201

    return project.json()["id"]


def test_file_version_history():
    token = create_user(
        "historyowner",
        "historyowner@example.com",
    )

    project_id = create_project(token)

    create = client.post(
        f"/projects/{project_id}/files",
        json={
            "path": "src/main.py",
            "language": "python",
            "content": "print('version 1')",
        },
        headers=auth(token),
    )

    assert create.status_code == 201

    file_id = create.json()["id"]

    update_2 = client.put(
        f"/projects/{project_id}/files/{file_id}",
        json={
            "content": "print('version 2')",
            "language": "python",
        },
        headers=auth(token),
    )

    assert update_2.status_code == 200

    update_3 = client.put(
        f"/projects/{project_id}/files/{file_id}",
        json={
            "content": "print('version 3')",
            "language": "python",
        },
        headers=auth(token),
    )

    assert update_3.status_code == 200

    history = client.get(
        f"/projects/{project_id}/files/{file_id}/versions",
        headers=auth(token),
    )

    assert history.status_code == 200

    versions = history.json()

    assert len(versions) == 3

    assert [version["version_number"] for version in versions] == [
        1,
        2,
        3,
    ]

    assert [version["content"] for version in versions] == [
        "print('version 1')",
        "print('version 2')",
        "print('version 3')",
    ]

    assert all(
        version["file_id"] == file_id
        for version in versions
    )


def test_version_history_isolated():
    owner_token = create_user(
        "historyowner2",
        "historyowner2@example.com",
    )

    outsider_token = create_user(
        "historyoutsider",
        "historyoutsider@example.com",
    )

    project_id = create_project(owner_token)

    create = client.post(
        f"/projects/{project_id}/files",
        json={
            "path": "private.py",
            "language": "python",
            "content": "secret = True",
        },
        headers=auth(owner_token),
    )

    assert create.status_code == 201

    file_id = create.json()["id"]

    denied = client.get(
        f"/projects/{project_id}/files/{file_id}/versions",
        headers=auth(outsider_token),
    )

    assert denied.status_code == 403


def test_missing_file_version_history():
    token = create_user(
        "historymissing",
        "historymissing@example.com",
    )

    project_id = create_project(token)

    response = client.get(
        f"/projects/{project_id}/files/999999/versions",
        headers=auth(token),
    )

    assert response.status_code == 404
