from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.websocket.ws_auth import authenticate_ws
from app.schemas.websocket import WSMessage
from app.websocket.manager import manager
from app.websocket.handlers import handle_ws_message
from app.config.logger import logger

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection attempt")

    db: Session = SessionLocal()

    try:
        # Authenticate WebSocket
        user = await authenticate_ws(websocket, db)
        if not user:
            logger.warning("WebSocket authentication failed")
            await websocket.close(code=1008)
            return

        logger.info(f"WebSocket authenticated | user_id={user.id}")

        # Connect user
        await manager.connect(user.id, websocket)
        logger.info(f"WebSocket connected | user_id={user.id}")

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            logger.debug(
                f"WebSocket message received | user_id={user.id} | payload={data}"
            )

            msg_type = data.get("type")
            if msg_type == "PING":
                await manager.send(user.id, {"type": "PONG", "payload": {}})
                logger.debug(f"PONG sent | user_id={user.id}")
                continue
            msg = WSMessage(**data)
            await handle_ws_message(user.id, msg)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected | user_id={getattr(user, 'id', None)}")
        manager.disconnect(getattr(user, "id", None))

    except Exception as e:
        logger.exception(
            f"WebSocket error | user_id={getattr(user, 'id', None)} | error={e}"
        )
        manager.disconnect(getattr(user, "id", None))

    finally:
        db.close()
        logger.debug("WebSocket DB session closed")
