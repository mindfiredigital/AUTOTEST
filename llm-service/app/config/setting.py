"""
Application settings and configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    PROJECT_NAME: str = "Autotest"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A FastAPI application for managing users"
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    ALLOWED_HOSTS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str

    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_HOST: str = "autotest_rabbitmq"
    RABBITMQ_PORT: str = "5672:5672"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
