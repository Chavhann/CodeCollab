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


def test_workspace_creation_and_listing():
    token = create_user(
        "workspaceowner",
        "workspaceowner@example.com",
    )

    create = client.post(
        "/workspaces",
        json={
            "name": "Engineering Workspace",
            "description": "CodeCollab engineering team",
        },
        headers=auth(token),
    )

    assert create.status_code == 201
    workspace = create.json()

    listing = client.get(
        "/workspaces",
        headers=auth(token),
    )

    assert listing.status_code == 200
    assert any(
        item["id"] == workspace["id"]
        for item in listing.json()
    )


def test_workspace_member_and_project_access():
    owner_token = create_user(
        "workspaceadmin",
        "workspaceadmin@example.com",
    )

    member_token = create_user(
        "workspacemember",
        "workspacemember@example.com",
    )

    owner_me = client.get(
        "/auth/me",
        headers=auth(owner_token),
    ).json()

    member_me = client.get(
        "/auth/me",
        headers=auth(member_token),
    ).json()

    workspace = client.post(
        "/workspaces",
        json={
            "name": "Collaboration Workspace",
        },
        headers=auth(owner_token),
    )

    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]

    add_member = client.post(
        f"/workspaces/{workspace_id}/members",
        json={
            "user_id": member_me["id"],
            "role": "member",
        },
        headers=auth(owner_token),
    )

    assert add_member.status_code == 201

    members = client.get(
        f"/workspaces/{workspace_id}/members",
        headers=auth(member_token),
    )

    assert members.status_code == 200
    assert len(members.json()) == 2

    project = client.post(
        f"/workspaces/{workspace_id}/projects",
        json={
            "name": "Realtime Editor",
            "description": "Collaborative editor project",
        },
        headers=auth(member_token),
    )

    assert project.status_code == 201

    projects = client.get(
        f"/workspaces/{workspace_id}/projects",
        headers=auth(member_token),
    )

    assert projects.status_code == 200
    assert projects.json()[0]["name"] == "Realtime Editor"


def test_workspace_isolation():
    owner_a = create_user(
        "isolateda",
        "isolateda@example.com",
    )

    owner_b = create_user(
        "isolatedb",
        "isolatedb@example.com",
    )

    workspace = client.post(
        "/workspaces",
        json={
            "name": "Private Workspace",
        },
        headers=auth(owner_a),
    )

    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]

    denied = client.get(
        f"/workspaces/{workspace_id}/members",
        headers=auth(owner_b),
    )

    assert denied.status_code == 403
