from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.auth_schema import RegisterRequest, RegisterResponse
from app.services.auth_service import auth_service
from app.db.session import get_db

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
