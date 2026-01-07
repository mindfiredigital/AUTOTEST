from typing import Any, Literal, Optional
from pydantic import BaseModel

WSMessageType = Literal[
    "PING",
    "PONG",
    "EVENT",
    "ERROR",
    "SUBSCRIBE",
    "UNSUBSCRIBE",
]

class WSMessage(BaseModel):
    type: WSMessageType
    payload: Any
    timestamp: Optional[int] = None
