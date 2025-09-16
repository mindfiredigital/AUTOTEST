from pydantic import BaseModel, EmailStr, Field
from pydantic import field_validator
from enum import Enum

class UserBase(BaseModel):
    username: str = Field(max_length=100)
    name: str | None = None
    email: EmailStr
    is_active: bool = True

class UserCreate(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=128)
    name: str | None = None
    email: EmailStr

class RoleName(str, Enum):
    Administrator = "Administrator"
    User = "User"

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role_type: str | None = None

    @field_validator("role_type")
    @classmethod
    def normalize_role(cls, v):
        if v is None:
            return v
        v_norm = v.strip().lower()
        if v_norm in ("admin", "administrator"):
            return "Administrator"
        if v_norm == "user":
            return "User"
        raise ValueError("role_type must be 'Admin' or 'User'")

class UserOut(UserBase):
    id: int
    role_id: int
    role_type: str  # new field
    username: str = Field(max_length=100)
    name: str | None = None
    email: EmailStr
    is_active: bool = True
