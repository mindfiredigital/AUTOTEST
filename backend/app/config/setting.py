from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Project Metadata Settings
    PROJECT_NAME: str = "Autotest"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A FastAPI application for managing users"
    ALLOWED_HOSTS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173","http://localhost:3000", "http://127.0.0.1:3000"]
    
    DATABASE_URL: str
    JWT_SECRET: str = "change_me"
    ALGO: str ="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int =5
    REFRESH_TOKEN_EXPIRE_MINUTES:int =60*2
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_NAME: str = "Admin User"
    ADMIN_EMAIL: str = "admin@example.com"
    HOST: str = "0.0.0.0"
    PORT:int = 8000
    DEBUG:bool = True
    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_HOST: str = "autotest_rabbitmq"
    RABBITMQ_PORT: int = 5672
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
