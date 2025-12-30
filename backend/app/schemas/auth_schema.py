from pydantic import BaseModel, EmailStr, field_validator, Field

# ---------------------------
# Register Request Schema
# ---------------------------
class RegisterRequest(BaseModel):
    firstname: str = Field(..., max_length=50)
    lastname: str = Field(..., max_length=50)
    email: str = EmailStr
    username:str= Field(...,max_length=50)
    password: str = Field(
        ...,
        min_length=6,
        max_length=50
    )


# ---------------------------
# Register Response Schema
# ---------------------------
class RegisterResponse(BaseModel):
    name: str
    email: str
    role: str

class LoginRequest(BaseModel):
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
