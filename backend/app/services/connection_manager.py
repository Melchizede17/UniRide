import uuid

from fastapi import WebSocket


class ConnectionManager:
    """In-memory registry of live WebSocket connections per user.

    A single-process registry: fine for local dev / one uvicorn worker. Would
    need a shared pub/sub (e.g. Redis) behind it to fan out across multiple
    backend processes/workers.
    """

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: uuid.UUID, payload: dict) -> None:
        for websocket in list(self._connections.get(user_id, ())):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(user_id, websocket)

    def is_connected(self, user_id: uuid.UUID) -> bool:
        return bool(self._connections.get(user_id))


connection_manager = ConnectionManager()
