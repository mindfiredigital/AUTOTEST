from fastapi import WebSocket
from typing import Dict
from app.config.logger import logger

class WSManager:
    def __init__(self):
        self.connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket
        logger.info(f"WebSocket connected | user_id={user_id} | total_connections={len(self.connections)}")

    def disconnect(self, user_id: int):
        if user_id in self.connections:
            self.connections.pop(user_id)
            logger.info(f"WebSocket disconnected | user_id={user_id} | total_connections={len(self.connections)}")
        else:
            logger.warning(f"Attempted to disconnect non-existent connection | user_id={user_id}")

    async def send(self, user_id: int, message: dict):
        ws = self.connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
                logger.debug(f"Sent WebSocket message | user_id={user_id} | message={message}")
            except Exception as e:
                logger.exception(f"Error sending WebSocket message | user_id={user_id} | error={e}")
        else:
            logger.warning(f"WebSocket send failed: no connection found | user_id={user_id}")

manager = WSManager()
