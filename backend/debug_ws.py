from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def register(username, email):
    r = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "CodeTest123!",
        },
    )
    print("register", username, r.status_code)

    r = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "CodeTest123!",
        },
    )
    print("login", username, r.status_code)
    return r.json()["access_token"]

print("1. Creating users")

owner_token = register(
    "crdtdebugowner",
    "crdtdebugowner@example.com",
)

member_token = register(
    "crdtdebugmember",
    "crdtdebugmember@example.com",
)

print("2. Creating workspace")

workspace = client.post(
    "/workspaces",
    json={"name": "CRDT Debug Workspace"},
    headers=auth(owner_token),
)
print("workspace:", workspace.status_code)
workspace_id = workspace.json()["id"]

member_info = client.get(
    "/auth/me",
    headers=auth(member_token),
)
member_id = member_info.json()["id"]

add_member = client.post(
    f"/workspaces/{workspace_id}/members",
    json={"user_id": member_id, "role": "member"},
    headers=auth(owner_token),
)
print("add member:", add_member.status_code)

print("3. Creating project")

project = client.post(
    f"/workspaces/{workspace_id}/projects",
    json={"name": "CRDT Debug Project"},
    headers=auth(owner_token),
)
print("project:", project.status_code)
project_id = project.json()["id"]

print("4. Creating file")

code_file = client.post(
    f"/projects/{project_id}/files",
    json={
        "path": "main.py",
        "language": "python",
        "content": "Hello",
    },
    headers=auth(owner_token),
)
print("file:", code_file.status_code)
file_id = code_file.json()["id"]

url = f"/ws/projects/{project_id}/files/{file_id}"

print("5. Connecting WebSocket A")

with client.websocket_connect(
    f"{url}?token={owner_token}"
) as websocket_a:

    print("A connected")
    print("A initial:", websocket_a.receive_json())

    print("6. Connecting WebSocket B")

    with client.websocket_connect(
        f"{url}?token={member_token}"
    ) as websocket_b:

        print("B connected")

        print("B initial:", websocket_b.receive_json())

        print("A presence:", websocket_a.receive_json())

        print("7. Sending CRDT insert")

        websocket_a.send_json(
            {
                "type": "crdt",
                "operation": {
                    "type": "insert",
                    "position": 5,
                    "text": " World",
                    "length": 0,
                    "operation_id": "debug-insert-1",
                    "client_id": "client-a",
                    "revision": 0,
                },
            }
        )

        print("8. Waiting for CRDT broadcast")

        message = websocket_b.receive_json()

        print("9. CRDT message:", message)

print("10. Finished")
