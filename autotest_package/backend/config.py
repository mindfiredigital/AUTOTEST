import os
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60

    # default admin
    admin_username: str = os.getenv("USERNAME", "admin")
    admin_password: str = os.getenv("PASSWORD", "Admin@123")
    admin_name: str = os.getenv("NAME", "Administrator")
    admin_email: EmailStr = os.getenv("EMAIL", "admin@example.com")

settings = Settings()
