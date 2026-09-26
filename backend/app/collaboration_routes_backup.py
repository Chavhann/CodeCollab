from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.collaboration import manager
from app.collaboration_schemas import CollaborationEvent
from app.crdt import CRDTDocument
from app.crdt_persistence import persist_document
from app.crdt_schemas import CRDTOperation
from app.database import SessionLocal
from app.file_routes import get_project_access
from app.models import User
from app.presence_schemas import CursorEvent, PresenceEvent
from app.security import decode_access_token


router = APIRouter()

documents: dict[str, CRDTDocument] = defaultdict(CRDTDocument)


def authenticate_websocket(websocket: WebSocket, db):
    token = websocket.query_params.get("token")

    if not token:
        return None

    try:
        user_id = decode_access_token(token)
    except (ValueError, TypeError):
        return None

    return db.get(User, user_id)


def get_file_room(project_id: int, file_id: int, user_id: int, db):
    user = db.get(User, user_id)

    if user is None:
        return None

    project, _ = get_project_access(
        project_id,
        user,
        db,
    )

    if project is None:
        return None

    return next(
        (file for file in project.files if file.id == file_id),
        None,
    )


def get_document(file_id: int, initial_content: str = ""):
    room = f"file:{file_id}"

    if room not in documents:
        documents[room] = CRDTDocument(initial_content)

    return documents[room]


@router.websocket("/ws/projects/{project_id}/files/{file_id}")
async def collaboration_websocket(
    websocket: WebSocket,
    project_id: int,
    file_id: int,
):
    room = f"file:{file_id}"
    user = None
    code_file = None

    db = SessionLocal()

    try:
        user = authenticate_websocket(websocket, db)

        if user is None:
            await websocket.close(code=1008)
            return

        code_file = get_file_room(
            project_id,
            file_id,
            user.id,
            db,
        )

        if code_file is None:
            await websocket.close(code=1008)
            return

        initial_content = (
            code_file.versions[-1].content
            if code_file.versions
            else ""
        )

    finally:
        db.close()

    document = get_document(
        file_id,
        initial_content,
    )

    try:
        await manager.connect(room, websocket)

        snapshot = document.snapshot()

        await websocket.send_json(
            {
                "type": "connected",
                "user_id": user.id,
                "username": user.username,
                "file_id": file_id,
                "content": snapshot.content,
                "revision": snapshot.revision,
            }
        )

        await manager.broadcast(
            room,
            {
                "type": "presence",
                "event": "joined",
                "user_id": user.id,
                "username": user.username,
                "connections": manager.room_size(room),
            },
            exclude=websocket,
        )

        while True:
            raw_event = await websocket.receive_json()
            event_type = raw_event.get("type")

            if event_type == "crdt":
                operation_data = raw_event.get("operation")

                if not isinstance(operation_data, dict):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Invalid CRDT operation",
                        }
                    )
                    continue

                try:
                    operation = CRDTOperation.model_validate(
                        operation_data
                    )
                except Exception:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Invalid CRDT operation",
                        }
                    )
                    continue

                result = document.apply_operation(operation)

                persistence_db = SessionLocal()

                try:
                    persisted_file = get_file_room(
                        project_id,
                        file_id,
                        user.id,
                        persistence_db,
                    )

                    if persisted_file is not None:
                        persist_document(
                            code_file=persisted_file,
                            document=document,
                            user_id=user.id,
                            db=persistence_db,
                        )
                finally:
                    persistence_db.close()

                await manager.broadcast(
                    room,
                    {
                        "type": "crdt",
                        "user_id": user.id,
                        "username": user.username,
                        "operation": operation.model_dump(),
                        "content": result.content,
                        "revision": result.revision,
                    },
                    exclude=websocket,
                )

            elif event_type == "cursor":
                event = CursorEvent.model_validate(raw_event)

                await manager.broadcast(
                    room,
                    {
                        "type": "cursor",
                        "user_id": user.id,
                        "username": user.username,
                        "cursor": event.cursor.model_dump(),
                        "selection_start": (
                            event.selection_start.model_dump()
                            if event.selection_start
                            else None
                        ),
                        "selection_end": (
                            event.selection_end.model_dump()
                            if event.selection_end
                            else None
                        ),
                    },
                    exclude=websocket,
                )

            elif event_type == "presence":
                event = PresenceEvent.model_validate(raw_event)

                await manager.broadcast(
                    room,
                    {
                        "type": "presence",
                        "event": "status",
                        "user_id": user.id,
                        "username": user.username,
                        "status": event.status,
                        "cursor": (
                            event.cursor.model_dump()
                            if event.cursor
                            else None
                        ),
                        "selection_start": (
                            event.selection_start.model_dump()
                            if event.selection_start
                            else None
                        ),
                        "selection_end": (
                            event.selection_end.model_dump()
                            if event.selection_end
                            else None
                        ),
                        "metadata": event.metadata,
                    },
                    exclude=websocket,
                )

            else:
                if (
                    "payload" in raw_event
                    and isinstance(raw_event["payload"], dict)
                ):
                    payload = raw_event["payload"]
                else:
                    payload = {
                        key: value
                        for key, value in raw_event.items()
                        if key != "type"
                    }

                event = CollaborationEvent(
                    type=event_type,
                    payload=payload,
                )

                await manager.broadcast(
                    room,
                    {
                        "type": "collaboration",
                        "event": event.type,
                        "user_id": user.id,
                        "username": user.username,
                        "payload": event.payload,
                    },
                    exclude=websocket,
                )

    except WebSocketDisconnect:
        pass

    finally:
        manager.disconnect(room, websocket)

        await manager.broadcast(
            room,
            {
                "type": "presence",
                "event": "left",
                "user_id": user.id,
                "username": user.username,
                "connections": manager.room_size(room),
            },
        )
