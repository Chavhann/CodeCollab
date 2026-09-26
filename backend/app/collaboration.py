from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, room: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms[room].add(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        connections = self.rooms.get(room)

        if not connections:
            return

        connections.discard(websocket)

        if not connections:
            self.rooms.pop(room, None)

    async def broadcast(
        self,
        room: str,
        message: dict,
        exclude: WebSocket | None = None,
    ):
        connections = self.rooms.get(room, set())

        disconnected = []

        for connection in connections:
            if connection is exclude:
                continue

            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(room, connection)

    def room_size(self, room: str) -> int:
        return len(self.rooms.get(room, set()))


manager = ConnectionManager()
