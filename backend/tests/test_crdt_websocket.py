import pytest
from fastapi.testclient import TestClient

from app.collaboration_routes import documents
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_crdt_documents():
    documents.clear()
    yield
    documents.clear()


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
    return {"Authorization": f"Bearer {token}"}


def create_shared_file(owner_token: str, member_token: str):
    workspace = client.post(
        "/workspaces",
        json={"name": "CRDT Workspace"},
        headers=auth(owner_token),
    )
    assert workspace.status_code == 201

    workspace_id = workspace.json()["id"]

    member = client.get(
        "/auth/me",
        headers=auth(member_token),
    )
    assert member.status_code == 200

    member_id = member.json()["id"]

    add_member = client.post(
        f"/workspaces/{workspace_id}/members",
        json={
            "user_id": member_id,
            "role": "member",
        },
        headers=auth(owner_token),
    )
    assert add_member.status_code == 201

    project = client.post(
        f"/workspaces/{workspace_id}/projects",
        json={"name": "CRDT Project"},
        headers=auth(owner_token),
    )
    assert project.status_code == 201

    project_id = project.json()["id"]

    code_file = client.post(
        f"/projects/{project_id}/files",
        json={
            "path": "main.py",
            "language": "python",
            "content": "Hello",
        },
        headers=auth(owner_token),
    )
    assert code_file.status_code == 201

    return project_id, code_file.json()["id"]


def test_crdt_insert_is_broadcast():
    owner_token = create_user(
        "crdtowner",
        "crdtowner@example.com",
    )

    member_token = create_user(
        "crdtmember",
        "crdtmember@example.com",
    )

    project_id, file_id = create_shared_file(
        owner_token,
        member_token,
    )

    url = f"/ws/projects/{project_id}/files/{file_id}"

    with client.websocket_connect(
        f"{url}?token={owner_token}"
    ) as websocket_a:

        initial = websocket_a.receive_json()

        assert initial["type"] == "connected"
        assert initial["content"] == "Hello"
        assert initial["revision"] == 0

        with client.websocket_connect(
            f"{url}?token={member_token}"
        ) as websocket_b:

            websocket_b.receive_json()
            websocket_a.receive_json()

            websocket_a.send_json(
                {
                    "type": "crdt",
                    "operation": {
                        "type": "insert",
                        "position": 5,
                        "text": " World",
                        "length": 0,
                        "operation_id": "insert-1",
                        "client_id": "client-a",
                        "revision": 0,
                    },
                }
            )

            message = websocket_b.receive_json()

            assert message["type"] == "crdt"
            assert message["operation"]["type"] == "insert"
            assert message["operation"]["text"] == " World"
            assert message["content"] == "Hello World"
            assert message["revision"] == 1


def test_crdt_delete_is_broadcast():
    owner_token = create_user(
        "crdtdeleteowner",
        "crdtdeleteowner@example.com",
    )

    member_token = create_user(
        "crdtdeletemember",
        "crdtdeletemember@example.com",
    )

    project_id, file_id = create_shared_file(
        owner_token,
        member_token,
    )

    url = f"/ws/projects/{project_id}/files/{file_id}"

    with client.websocket_connect(
        f"{url}?token={owner_token}"
    ) as websocket_a:

        websocket_a.receive_json()

        with client.websocket_connect(
            f"{url}?token={member_token}"
        ) as websocket_b:

            websocket_b.receive_json()
            websocket_a.receive_json()

            websocket_a.send_json(
                {
                    "type": "crdt",
                    "operation": {
                        "type": "delete",
                        "position": 0,
                        "text": "",
                        "length": 5,
                        "operation_id": "delete-1",
                        "client_id": "client-a",
                        "revision": 0,
                    },
                }
            )

            message = websocket_b.receive_json()

            assert message["type"] == "crdt"
            assert message["operation"]["type"] == "delete"
            assert message["content"] == ""
            assert message["revision"] == 1


def test_crdt_duplicate_operation_does_not_increment_revision():
    owner_token = create_user(
        "crdtdupeowner",
        "crdtdupeowner@example.com",
    )

    member_token = create_user(
        "crdtdupemember",
        "crdtdupemember@example.com",
    )

    project_id, file_id = create_shared_file(
        owner_token,
        member_token,
    )

    url = f"/ws/projects/{project_id}/files/{file_id}"

    with client.websocket_connect(
        f"{url}?token={owner_token}"
    ) as websocket_a:

        websocket_a.receive_json()

        with client.websocket_connect(
            f"{url}?token={member_token}"
        ) as websocket_b:

            websocket_b.receive_json()
            websocket_a.receive_json()

            operation = {
                "type": "crdt",
                "operation": {
                    "type": "insert",
                    "position": 5,
                    "text": "!",
                    "length": 0,
                    "operation_id": "duplicate-1",
                    "client_id": "client-a",
                    "revision": 0,
                },
            }

            websocket_a.send_json(operation)

            first = websocket_b.receive_json()

            assert first["content"] == "Hello!"
            assert first["revision"] == 1

            websocket_a.send_json(operation)

            second = websocket_b.receive_json()

            assert second["content"] == "Hello!"
            assert second["revision"] == 1


def test_crdt_invalid_operation_returns_error():
    owner_token = create_user(
        "crdtinvalidowner",
        "crdtinvalidowner@example.com",
    )

    member_token = create_user(
        "crdtinvalidmember",
        "crdtinvalidmember@example.com",
    )

    project_id, file_id = create_shared_file(
        owner_token,
        member_token,
    )

    url = f"/ws/projects/{project_id}/files/{file_id}"

    with client.websocket_connect(
        f"{url}?token={owner_token}"
    ) as websocket:

        websocket.receive_json()

        websocket.send_json(
            {
                "type": "crdt",
                "operation": {
                    "type": "invalid",
                    "position": 0,
                    "operation_id": "bad-1",
                    "client_id": "client-a",
                },
            }
        )

        error = websocket.receive_json()

        assert error["type"] == "error"
        assert error["message"] == "Invalid CRDT operation"
