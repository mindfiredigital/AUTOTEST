"""
Application settings and configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Database
    DATABASE_URL: str

    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_HOST: str = "autotest_rabbitmq"
    RABBITMQ_PORT: str = "5672:5672"
    SITE_ANALYSE_QUEUE: str
    PAGE_EXTRACT_QUEUE: str
    LLM_QUEUE: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
