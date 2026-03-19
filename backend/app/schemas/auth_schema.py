import re
from pydantic import BaseModel, EmailStr, field_validator, Field
from pydantic import ConfigDict

_PASSWORD_RE = re.compile(
    r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,}$'
)

# ---------------------------
# Register Request Schema
# ---------------------------
class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    firstname: str = Field(..., max_length=50)
    lastname: str = Field(..., max_length=50)
    email: str = EmailStr
    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not _PASSWORD_RE.match(value):
            raise ValueError(
                "Password must be at least 8 characters and include an uppercase letter, "
                "a lowercase letter, a digit, and a special character."
            )
        return value


# ---------------------------
# Register Response Schema
# ---------------------------
class RegisterResponse(BaseModel):
    name: str
    email: str
    role: str

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str

    @field_validator("email")
    def normalize_email(cls, value):
        return value.strip().lower()

    @field_validator("password")
    def validate_password(cls, value):
        if not value.strip():
            raise ValueError("Password cannot be empty")
        return value

class LoginResponse(BaseModel):
    name: str
    email: str
    role: str
