from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Project Metadata Settings
    PROJECT_NAME: str = "Autotest"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A FastAPI application for managing users"
    ALLOWED_HOSTS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173","http://localhost:3000", "http://127.0.0.1:3000"]
    
    DATABASE_URL: str
    JWT_SECRET: str
    ALGO: str ="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int =5
    REFRESH_TOKEN_EXPIRE_MINUTES:int =60*2

    HOST: str = "0.0.0.0"
    PORT:int = 8000
    DEBUG:bool = False

    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
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
    PAGE_AUTH_UPDATE_QUEUE: str
    AUTH_CREDENTIAL_UPDATE_QUEUE: str
    PAGE_AUTH_UPDATE_QUEUE: str
    SITE_STATUS_UPDATE_QUEUE: str
    TEST_SUITE_EXECUTION_QUEUE: str
    PAGE_ANALYSE_QUEUE: str
    PROCESSPAGE_EXTRACT_SINGLE_QUEUE: str
    TEST_SUITE_QUEUE: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
