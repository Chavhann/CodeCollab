from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

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
    return {"Authorization": f"Bearer {token}"}


def create_file(token: str):
    workspace = client.post(
        "/workspaces",
        json={"name": "WebSocket Workspace"},
        headers=auth(token),
    )

    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]

    project = client.post(
        f"/workspaces/{workspace_id}/projects",
        json={"name": "Realtime Project"},
        headers=auth(token),
    )

    assert project.status_code == 201
    project_id = project.json()["id"]

    code_file = client.post(
        f"/projects/{project_id}/files",
        json={
            "path": "src/main.py",
            "language": "python",
            "content": "print('hello')",
        },
        headers=auth(token),
    )

    assert code_file.status_code == 201

    return workspace_id, project_id, code_file.json()["id"]


def add_workspace_member(owner_token: str, workspace_id: int, member_token: str):
    me = client.get(
        "/auth/me",
        headers=auth(member_token),
    )

    assert me.status_code == 200
    member_user_id = me.json()["id"]

    response = client.post(
        f"/workspaces/{workspace_id}/members",
        json={
            "user_id": member_user_id,
            "role": "member",
        },
        headers=auth(owner_token),
    )

    assert response.status_code == 201


def test_websocket_connection_and_message_broadcast():
    token_a = create_user(
        "wsusera",
        "wsusera@example.com",
    )

    token_b = create_user(
        "wsuserb",
        "wsuserb@example.com",
    )

    workspace_id, project_id, file_id = create_file(token_a)

    add_workspace_member(
        token_a,
        workspace_id,
        token_b,
    )

    ws_url = f"/ws/projects/{project_id}/files/{file_id}"

    with client.websocket_connect(
        f"{ws_url}?token={token_a}"
    ) as websocket_a:

        connected_a = websocket_a.receive_json()

        assert connected_a["type"] == "connected"
        assert connected_a["username"] == "wsusera"

        with client.websocket_connect(
            f"{ws_url}?token={token_b}"
        ) as websocket_b:

            connected_b = websocket_b.receive_json()

            assert connected_b["type"] == "connected"
            assert connected_b["username"] == "wsuserb"

            joined = websocket_a.receive_json()

            assert joined["type"] == "presence"
            assert joined["event"] == "joined"
            assert joined["username"] == "wsuserb"
            assert joined["connections"] == 2

            websocket_a.send_json(
                {
                    "type": "code_change",
                    "path": "src/main.py",
                    "content": "print('updated')",
                }
            )

            message = websocket_b.receive_json()

            assert message["type"] == "collaboration"
            assert message["event"] == "code_change"
            assert message["username"] == "wsusera"
            assert message["payload"]["path"] == "src/main.py"
            assert message["payload"]["content"] == "print('updated')"


def test_websocket_rejects_invalid_token():
    token = create_user(
        "wsinvalid",
        "wsinvalid@example.com",
    )

    _, project_id, file_id = create_file(token)

    try:
        with client.websocket_connect(
            f"/ws/projects/{project_id}/files/{file_id}?token=invalid-token"
        ):
            assert False, "Invalid token should be rejected"
    except WebSocketDisconnect as exc:
        assert exc.code == 1008


def test_websocket_rejects_missing_file():
    token = create_user(
        "wsmissing",
        "wsmissing@example.com",
    )

    _, project_id, _ = create_file(token)

    try:
        with client.websocket_connect(
            f"/ws/projects/{project_id}/files/999999?token={token}"
        ):
            assert False, "Missing file should be rejected"
    except WebSocketDisconnect as exc:
        assert exc.code == 1008
