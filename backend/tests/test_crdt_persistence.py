from fastapi.testclient import TestClient

from app.crdt import CRDTDocument
from app.crdt_persistence import load_document, persist_document
from app.main import app
from app.database import SessionLocal
from app.models import CodeFile


client = TestClient(app)


def auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_crdt_persistence():
    register = client.post(
        "/auth/register",
        json={
            "username": "persistowner",
            "email": "persistowner@example.com",
            "password": "CodeTest123!",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "persistowner@example.com",
            "password": "CodeTest123!",
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    workspace = client.post(
        "/workspaces",
        json={"name": "Persistence Workspace"},
        headers=auth(token),
    )
    assert workspace.status_code == 201

    workspace_id = workspace.json()["id"]

    project = client.post(
        f"/workspaces/{workspace_id}/projects",
        json={"name": "Persistence Project"},
        headers=auth(token),
    )
    assert project.status_code == 201

    project_id = project.json()["id"]

    code_file_response = client.post(
        f"/projects/{project_id}/files",
        json={
            "path": "persistent.py",
            "language": "python",
            "content": "Persistent content",
        },
        headers=auth(token),
    )
    assert code_file_response.status_code == 201

    file_id = code_file_response.json()["id"]

    db = SessionLocal()

    try:
        code_file = db.get(CodeFile, file_id)

        assert code_file is not None

        document = CRDTDocument("Persistent content")

        document.apply_insert(
            position=len(document.content),
            text="!",
            operation_id="persistence-test-1",
        )

        version = persist_document(
            code_file=code_file,
            document=document,
            user_id=code_file.project.workspace.owner_id,
            db=db,
        )

        assert version.content == "Persistent content!"
        assert version.version_number >= 1

        loaded = load_document(code_file, db)

        assert loaded.content == "Persistent content!"
        assert loaded.revision == 0

    finally:
        db.close()
