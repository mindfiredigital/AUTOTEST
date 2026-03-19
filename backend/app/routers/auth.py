"""Authentication routes: register, login, refresh, get current user, logout."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import Response, Request
from shared_orm.models.user import User

from app.schemas.auth_schema import RegisterRequest, RegisterResponse,LoginRequest, LoginResponse
from app.services.auth_service import auth_service
from app.config.database import get_db
from app.middleware.auth_middleware import auth_required

router = APIRouter(
    tags=["Authentication"]
)


@router.post("/register", response_model=RegisterResponse)
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    - Create username 
    - Check email/username uniqueness
    - Save user in DB
    - Return name, email, and role
    """
    return auth_service.register(data, db)

@router.post("/login", response_model=LoginResponse)
def login_user(response: Response, data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login a user using email + password.
    """
    return auth_service.login(response, data, db)


@router.post("/refresh")
def refresh_token(request: Request, response: Response):
    """Refresh authentication tokens using the incoming request.

    Delegates to the auth service which issues new access/refresh
    tokens as needed.
    """
    return auth_service.refresh(request, response)


@router.get("/me")
def get_me(request: Request, db: Session = Depends(get_db), current_user: User = Depends(auth_required)):
    """Return the profile of the currently authenticated user."""
    return auth_service.get_me(request, db, current_user)


@router.post("/logout")
def logout(response: Response):
    """Log out the user and clear authentication cookies/tokens."""
    return auth_service.logout(response)