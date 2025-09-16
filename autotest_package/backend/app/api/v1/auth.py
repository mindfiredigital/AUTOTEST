from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.deps import get_db, get_current_user_claims
from app.models.user import User
from app.schemas.auth import Token
from app.core.security import verify_password, create_access_token
from app.models.role import Role

from app.db.seed import ADMIN_ACCESS, USER_ACCESS

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == form_data.username)).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.username, user_id=user.id, role_id=user.role_id)
    return Token(access_token=token)

# @router.get("/access-modules")
# def get_access_modules(claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
#     role_id = claims.get("role_id")
#     # prefer DB source of truth to reflect any changes in Role.access
#     row = db.execute(select(Role.type, Role.access).where(Role.id == role_id)).first()
#     if not row:
#         return {"role_id": role_id, "role_type": "Unknown", "modules": []}
#     role_type, access = row, row[1]
#     modules = []
#     if isinstance(access, dict):
#         # assume {"modules": [...]} as seeded
#         modules = access.get("modules", [])
#     return {"role_id": role_id, "role_type": role_type, "modules": modules}

@router.get("/access-modules")
def get_access_modules(claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
    role_id = claims.get("role_id")
    row = db.execute(
        select(Role.type, Role.access).where(Role.id == role_id)
    ).first()
    if not row:
        return {"role_id": role_id, "role_type": "Unknown", "modules": []}
    # Row unpack (either works):
    # role_type, access = row, row[1]
    m = row._mapping
    role_type, access = m["type"], m["access"]

    modules = []
    if isinstance(access, dict):
        modules = access.get("modules", [])
    # Return only JSON-native types
    return {
        "role_id": role_id,
        "role_type": role_type,
        "modules": modules,
    }
