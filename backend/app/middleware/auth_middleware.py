from fastapi import Request, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.config.security import security_service
import jwt


class AuthDependency:
    """
    Class-based dependency to validate JWT from cookies,
    clear cookies on invalid/expired token or inactive user,
    and return the authenticated user.
    """

    def __call__(self, request: Request, response: Response, db: Session = Depends(get_db)):
        token = request.cookies.get("access_token")

        def clear_tokens():
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")

        if not token:
            clear_tokens()
            raise HTTPException(status_code=401, detail="Missing authentication token")

        try:
            payload = security_service.decode_token(token)
            email = payload.get("sub")

            if email is None:
                clear_tokens()
                raise HTTPException(status_code=401, detail="Invalid token payload")

        except jwt.ExpiredSignatureError:
            clear_tokens()
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            clear_tokens()
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            clear_tokens()
            raise HTTPException(status_code=401, detail="User not found")

        if not getattr(user, "is_active", True):
            clear_tokens()
            raise HTTPException(status_code=403, detail="User is inactive")

        return user


auth_required = AuthDependency()
