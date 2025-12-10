from pydantic import BaseModel

# ---------------------------
# Register Request Schema
# ---------------------------
class RegisterRequest(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str


# ---------------------------
# Register Response Schema
# ---------------------------
class RegisterResponse(BaseModel):
    name: str
    email: str
    role: str
