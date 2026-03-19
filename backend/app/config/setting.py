from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List
import logging
import warnings

logger = logging.getLogger(__name__)

_INSECURE_JWT_DEFAULTS = {"change_me", "secret", "changeme", "your-secret-key", ""}
_INSECURE_ADMIN_PASSWORDS = {"Admin@123", "admin", "password", "admin123", ""}

class Settings(BaseSettings):
    # Project Metadata Settings
    PROJECT_NAME: str = "Autotest"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A FastAPI application for managing users"
    ALLOWED_HOSTS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173","http://localhost:3000", "http://127.0.0.1:3000"]

    DATABASE_URL: str
    JWT_SECRET: str  # No default — must be set in .env
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
    ENVIRONMENT: str = "development"

    @model_validator(mode="after")
    def enforce_secret_security(self) -> "Settings":
        is_production = self.ENVIRONMENT.lower() == "production"

        if self.JWT_SECRET.lower() in _INSECURE_JWT_DEFAULTS:
            raise ValueError(
                "JWT_SECRET is not set or uses an insecure default value. "
                "Set a strong random secret in your .env file. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if self.ADMIN_PASSWORD in _INSECURE_ADMIN_PASSWORDS:
            if is_production:
                raise ValueError(
                    "[SECURITY] ADMIN_PASSWORD is set to an insecure default in production. "
                    "Set a strong ADMIN_PASSWORD in your .env file before deploying."
                )
            warnings.warn(
                "[SECURITY] ADMIN_PASSWORD is set to an insecure default. "
                "Change it in your .env file before deploying to production.",
                stacklevel=2,
            )
        return self
    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_HOST: str = "autotest_rabbitmq"
    RABBITMQ_PORT: str = "5672:5672"
    SITE_ANALYSE_QUEUE: str
    PAGE_EXTRACT_QUEUE: str
    PAGE_EXTRACT_SINGLE_QUEUE: str
    LLM_QUEUE: str
    TEST_SCRIPT_QUEUE: str
    SCENARIO_RERUN_QUEUE: str
    TEST_EXECUTION_QUEUE: str
    TEST_CASE_QUEUE: str
    PAGE_STATUS_UPDATE_QUEUE: str
    TEST_SCENARIO_QUEUE: str
    TEST_SCRIPT_QUEUE: str
    PAGE_AUTH_UPDATE_QUEUE: str
    AUTH_CREDENTIAL_UPDATE_QUEUE: str

    PAGE_AUTH_UPDATE_QUEUE: str
    AUTH_CREDENTIAL_UPDATE_QUEUE: str
    SITE_STATUS_UPDATE_QUEUE: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
