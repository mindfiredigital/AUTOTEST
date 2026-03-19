# app/websocket/router.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.websocket.ws_auth import authenticate_ws
from app.websocket.manager import manager
from app.websocket.handlers import handle_ws_message
from app.schemas.websocket import WSMessage
from app.config.logger import logger

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    logger.info("[WS] Connection attempt")

    user = await authenticate_ws(websocket, db)
    if not user:
        return

    await manager.connect(user.id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            msg = WSMessage(**data)
            await handle_ws_message(user.id, msg)

    except WebSocketDisconnect:
        logger.info(f"[WS] Disconnected | user_id={user.id}")
        manager.disconnect(user.id, websocket)

    except Exception as e:
        logger.exception(
            f"[WS] Error | user_id={user.id} | error={e}"
        )
        manager.disconnect(user.id, websocket)