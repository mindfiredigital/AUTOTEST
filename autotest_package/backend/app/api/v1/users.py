from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.deps import get_db, get_current_user_claims
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.models.user import User
from app.models.role import Role
from app.core.security import hash_password

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def is_admin(claims: dict) -> bool:
    return claims.get("role_id") == 1  # role_id=1 => Admin

def _normalize_role_name(v: str) -> str:
    # accept Admin/Administrator/User, store as Administrator or User (as per XLSX)
    nv = v.strip().lower()
    if nv in ("admin", "administrator"):
        return "Administrator"
    if nv == "user":
        return "User"
    raise ValueError("role_type must be 'Admin' or 'User'")

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # role_id->2 by default
    if db.execute(select(User).where((User.username == payload.username) | (User.email == payload.email))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    new_user = User(
        role_id=2,
        username=payload.username,
        password=hash_password(payload.password),
        name=payload.name,
        email=payload.email,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # fetch role_type to satisfy response schema
    role_type = db.execute(select(Role.type).where(Role.id == new_user.role_id)).scalar_one()
    return UserOut(id=new_user.id, role_id=new_user.role_id, role_type=role_type, username=new_user.username, name=new_user.name, email=new_user.email, is_active=new_user.is_active)

@router.get("/", response_model=list[UserOut])
def list_users(claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
    if not is_admin(claims):
        raise HTTPException(status_code=403, detail="Admin access required")
    #rows = db.execute(select(User)).scalars().all()
    rows = db.execute(
        select(User, Role.type.label("role_type")).join(Role, Role.id == User.role_id)
    ).all()
    return [UserOut(id=u.id, role_id=u.role_id, role_type=rt, username=u.username, name=u.name, email=u.email, is_active=u.is_active) for (u, rt) in rows]

# @router.get("/{user_id}", response_model=UserOut)
# def get_user(user_id: int, claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
#     # Admin can view anyone; User can view only self
#     if not is_admin(claims) and claims.get("user_id") != user_id:
#         raise HTTPException(status_code=403, detail="Not permitted")
#     # u = db.get(User, user_id)
#     # if not u:
#     #     raise HTTPException(status_code=404, detail="User not found")
#     # eager join to get role.type
#     row = db.execute(
#         select(User, Role.type.label("role_type")).join(Role, Role.id == User.role_id).where(User.id == user_id)
#     ).first()
#     if not row:
#         raise HTTPException(status_code=404, detail="User not found")
#     u, role_type = row, row[1]
#     return UserOut(id=u.id, role_id=u.role_id, role_type=role_type, username=u.username, name=u.name, email=u.email, is_active=u.is_active)

# @router.get("/{user_id}", response_model=UserOut)
# def get_user(user_id: int, claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
#     if not is_admin(claims) and claims.get("user_id") != user_id:
#         raise HTTPException(status_code=403, detail="Not permitted")

#     row = db.execute(
#         select(User, Role.type.label("role_type"))
#         .join(Role, Role.id == User.role_id)
#         .where(User.id == user_id)
#     ).first()

#     if not row:
#         raise HTTPException(status_code=404, detail="User not found")

#     u, role_type = row, row[1]  # tuple-unpack from Row
#     return UserOut(
#         id=u.id, role_id=u.role_id, role_type=role_type,
#         username=u.username, name=u.name, email=u.email, is_active=u.is_active
#     )

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
    if not is_admin(claims) and claims.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not permitted")

    u = db.execute(select(User).where(User.id == user_id)).scalars().one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    role_type = db.execute(select(Role.type).where(Role.id == u.role_id)).scalar_one()
    return UserOut(
        id=u.id,
        role_id=u.role_id,
        role_type=role_type,
        username=u.username,
        name=u.name,
        email=u.email,
        is_active=u.is_active,
    )

# @router.patch("/{user_id}", response_model=UserOut)
# def update_user(user_id: int, payload: UserUpdate, claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
#     # Admin can edit anyone; User can edit only self
#     if not is_admin(claims) and claims.get("user_id") != user_id:
#         raise HTTPException(status_code=403, detail="Not permitted")
#     u = db.get(User, user_id)
#     if not u:
#         raise HTTPException(status_code=404, detail="User not found")

#     if payload.email and payload.email != u.email:
#         exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
#         if exists:
#             raise HTTPException(status_code=400, detail="Email already in use")
#         u.email = payload.email
#     if payload.name is not None:
#         u.name = payload.name
#     if payload.is_active is not None:
#         # Only Admin should be able to toggle is_active; enforce
#         if not is_admin(claims):
#             raise HTTPException(status_code=403, detail="Only Admin can change activation")
#         u.is_active = payload.is_active
#     if payload.password:
#         u.password = hash_password(payload.password)

#     db.add(u)
#     db.commit()
#     db.refresh(u)
#     return UserOut(id=u.id, role_id=u.role_id, username=u.username, name=u.name, email=u.email, is_active=u.is_active)

# @router.patch("/{user_id}", response_model=UserOut)
# def update_user(user_id: int, payload: UserUpdate, claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
#     if not is_admin(claims) and claims.get("user_id") != user_id:
#         raise HTTPException(status_code=403, detail="Not permitted")
#     u = db.get(User, user_id)
#     if not u:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Email uniqueness
#     if payload.email and payload.email != u.email:
#         exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
#         if exists:
#             raise HTTPException(status_code=400, detail="Email already in use")
#         u.email = payload.email

#     # Name/password updates
#     if payload.name is not None:
#         u.name = payload.name
#     if payload.password:
#         u.password = hash_password(payload.password)

#     # is_active is Admin-only
#     if payload.is_active is not None:
#         if not is_admin(claims):
#             raise HTTPException(status_code=403, detail="Only Admin can change activation")
#         u.is_active = payload.is_active

#     # role_type is Admin-only: accepts "Admin" or "User" in request but stores "Administrator"/"User"
#     if payload.role_type is not None:
#         if not is_admin(claims):
#             raise HTTPException(status_code=403, detail="Only Admin can change role_type")
#         # Map RoleName to Role.id
#         desired = "Administrator" if str(payload.role_type) == "RoleName.Administrator" else "User"
#         role = db.execute(select(Role).where(Role.type == desired)).scalar_one_or_none()
#         if not role:
#             raise HTTPException(status_code=400, detail="Invalid role_type")
#         u.role_id = role.id

#     db.add(u)
#     db.commit()
#     db.refresh(u)

#     # Return with role_type joined
#     rt = db.execute(select(Role.type).where(Role.id == u.role_id)).scalar_one()
#     return UserOut(
#         id=u.id, role_id=u.role_id, role_type=rt,
#         username=u.username, name=u.name, email=u.email, is_active=u.is_active
#     )


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
    if not is_admin(claims) and claims.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not permitted")
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # Email uniqueness
    if payload.email and payload.email != u.email:
        exists = db.execute(select(User.id).where(User.email == payload.email)).scalar_one_or_none()
        if exists:
            raise HTTPException(status_code=400, detail="Email already in use")
        u.email = payload.email

    # Name/password
    if payload.name is not None:
        u.name = payload.name
    if payload.password:
        u.password = hash_password(payload.password)

    # is_active is Admin-only
    if payload.is_active is not None:
        if not is_admin(claims):
            raise HTTPException(status_code=403, detail="Only Admin can change activation")
        u.is_active = payload.is_active

    # role_type is Admin-only
    if payload.role_type is not None:
        if not is_admin(claims):
            raise HTTPException(status_code=403, detail="Only Admin can change role_type")
        desired_name = _normalize_role_name(payload.role_type if isinstance(payload.role_type, str) else payload.role_type.value)
        role_row = db.execute(select(Role).where(Role.type == desired_name)).scalar_one_or_none()
        if not role_row:
            raise HTTPException(status_code=400, detail="Invalid role_type")
        u.role_id = role_row.id

    db.commit()
    db.refresh(u)

    # fetch role_type to return
    rt = db.execute(select(Role.type).where(Role.id == u.role_id)).scalar_one()
    return UserOut(
        id=u.id, role_id=u.role_id, role_type=rt,
        username=u.username, name=u.name, email=u.email, is_active=u.is_active
    )
