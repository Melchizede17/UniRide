from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_current_user_ws
from app.models import User
from app.services.connection_manager import connection_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/matches")
async def matches_websocket(websocket: WebSocket, current_user: User = Depends(get_current_user_ws)) -> None:
    await connection_manager.connect(current_user.id, websocket)
    try:
        while True:
            # Clients don't need to send anything meaningful; just keep the
            # socket open and drain whatever frames arrive (e.g. keepalive pings).
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(current_user.id, websocket)
