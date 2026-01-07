from fastapi import WebSocket, status
from sqlalchemy.orm import Session
import jwt

from app.db.session import get_db
from shared_orm.models.user import User
from app.config.security import security_service
from app.config.logger import logger


async def authenticate_ws(websocket: WebSocket, db: Session) -> User | None:
    """
    Authenticate a WebSocket connection using HttpOnly cookies.

    Args:
        websocket (WebSocket): The WebSocket connection
        db (Session): SQLAlchemy database session

    Returns:
        User | None: Authenticated User object or None if authentication fails
    """

    token = websocket.cookies.get("access_token")
    if not token:
        logger.warning("WebSocket auth failed: no access token in cookies")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        payload = security_service.decode_token(token)
        email = payload.get("sub")

        if not email:
            logger.warning("WebSocket auth failed: token payload missing 'sub'")
            raise Exception("Invalid payload")

    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket auth failed: token expired")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    except jwt.InvalidTokenError:
        logger.warning("WebSocket auth failed: invalid token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during WS authentication: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return None

    user = db.query(User).filter(User.email == email).first()

    if not user:
        logger.warning(f"WebSocket auth failed: no user found for email={email}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    if not user.is_active:
        logger.warning(f"WebSocket auth failed: user inactive | email={email}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    logger.info(f"WebSocket authenticated | user_id={user.id} | email={email}")
    return user
