from app.schemas.websocket import WSMessage
from app.websocket.manager import manager
from app.config.logger import logger


async def handle_ws_message(user_id: int, msg: WSMessage) -> None:
    """
    Handle incoming WebSocket messages for a connected user.

    Args:
        user_id (int): Authenticated user ID
        msg (WSMessage): Incoming WebSocket message
    """

    logger.debug(
        f"Handling WS message | user_id={user_id} | type={msg.type}"
    )

    if msg.type == "PING":
        logger.debug(f"PING received | user_id={user_id}")

        await manager.send(
            user_id,
            {"type": "PONG", "payload": {}}
        )

        logger.debug(f"PONG sent | user_id={user_id}")

    elif msg.type == "EVENT":
        logger.info(
            f"EVENT received | user_id={user_id} | payload={msg.payload}"
        )

        await manager.send(
            user_id,
            {"type": "EVENT", "payload": msg.payload}
        )

        logger.info(f"EVENT echoed | user_id={user_id}")

    else:
        logger.warning(
            f"Unknown WS message type | user_id={user_id} | type={msg.type}"
        )
