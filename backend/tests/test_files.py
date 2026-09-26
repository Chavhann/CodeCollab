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


def create_workspace_and_project(token: str):
    workspace = client.post(
        "/workspaces",
        json={
            "name": "File Test Workspace",
            "description": "Workspace for file API tests",
        },
        headers=auth(token),
    )

    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]

    project = client.post(
        f"/workspaces/{workspace_id}/projects",
        json={
            "name": "CodeCollab Editor",
            "description": "File management project",
        },
        headers=auth(token),
    )

    assert project.status_code == 201

    return project.json()["id"]


def test_create_and_list_files():
    token = create_user(
        "fileowner",
        "fileowner@example.com",
    )

    project_id = create_workspace_and_project(token)

    create = client.post(
        f"/projects/{project_id}/files",
        json={
            "path": "src/main.py",
            "language": "python",
            "content": "print('Hello CodeCollab')",
        },
        headers=auth(token),
    )

    assert create.status_code == 201

    file_data = create.json()

    assert file_data["path"] == "src/main.py"
    assert file_data["language"] == "python"
    assert file_data["content"] == "print('Hello CodeCollab')"
    assert file_data["version_number"] == 1

    listing = client.get(
        f"/projects/{project_id}/files",
        headers=auth(token),
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["path"] == "src/main.py"


def test_duplicate_file_is_rejected():
    token = create_user(
        "duplicateowner",
        "duplicateowner@example.com",
    )

    project_id = create_workspace_and_project(token)

    payload = {
        "path": "README.md",
        "language": "markdown",
        "content": "# CodeCollab",
    }

    first = client.post(
        f"/projects/{project_id}/files",
        json=payload,
        headers=auth(token),
    )

    assert first.status_code == 201

    second = client.post(
        f"/projects/{project_id}/files",
        json=payload,
        headers=auth(token),
    )

    assert second.status_code == 409


def test_file_update_creates_new_version():
    token = create_user(
        "versionowner",
        "versionowner@example.com",
    )

    project_id = create_workspace_and_project(token)

    create = client.post(
        f"/projects/{project_id}/files",
        json={
            "path": "src/app.py",
            "language": "python",
            "content": "print('version 1')",
        },
        headers=auth(token),
    )

    assert create.status_code == 201

    file_id = create.json()["id"]

    update = client.put(
        f"/projects/{project_id}/files/{file_id}",
        json={
            "content": "print('version 2')",
            "language": "python",
        },
        headers=auth(token),
    )

    assert update.status_code == 200

    updated = update.json()

    assert updated["content"] == "print('version 2')"
    assert updated["version_number"] == 2

    get_file = client.get(
        f"/projects/{project_id}/files/{file_id}",
        headers=auth(token),
    )

    assert get_file.status_code == 200
    assert get_file.json()["content"] == "print('version 2')"
    assert get_file.json()["version_number"] == 2


def test_project_access_isolation():
    owner_token = create_user(
        "fileisolatedowner",
        "fileisolatedowner@example.com",
    )

    outsider_token = create_user(
        "fileoutsider",
        "fileoutsider@example.com",
    )

    project_id = create_workspace_and_project(owner_token)

    denied = client.get(
        f"/projects/{project_id}/files",
        headers=auth(outsider_token),
    )

    assert denied.status_code == 403


def test_admin_can_delete_file():
    token = create_user(
        "deleteadmin",
        "deleteadmin@example.com",
    )

    project_id = create_workspace_and_project(token)

    create = client.post(
        f"/projects/{project_id}/files",
        json={
            "path": "delete.py",
            "language": "python",
            "content": "print('delete me')",
        },
        headers=auth(token),
    )

    assert create.status_code == 201
    file_id = create.json()["id"]

    delete = client.delete(
        f"/projects/{project_id}/files/{file_id}",
        headers=auth(token),
    )

    assert delete.status_code == 204

    get_file = client.get(
        f"/projects/{project_id}/files/{file_id}",
        headers=auth(token),
    )

    assert get_file.status_code == 404
