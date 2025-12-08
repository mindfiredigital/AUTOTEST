from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Project Metadata Settings
    PROJECT_NAME: str = "Autotest"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A FastAPI application for managing users"
    ALLOWED_HOSTS: List[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
    
    DATABASE_URL: str
    JWT_SECRET: str = "change_me"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_NAME: str = "Admin User"
    ADMIN_EMAIL: str = "admin@example.com"
    HOST: str = "0.0.0.0"
    PORT:int = 8000
    DEBUG:bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
