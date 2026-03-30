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
    PAGE_ANALYSE_QUEUE: str
    TEST_SCENARIO_QUEUE: str
    TEST_CASE_QUEUE:str
    PAGE_EXTRACT_SINGLE_QUEUE:str
    TEST_SCRIPT_QUEUE: str
    TEST_EXECUTION_QUEUE: str
    LLM_QUEUE: str
    SCENARIO_RERUN_QUEUE: str
    PAGE_STATUS_UPDATE_QUEUE: str
    PAGE_AUTH_UPDATE_QUEUE: str
    AUTH_CREDENTIAL_UPDATE_QUEUE: str
    SITE_STATUS_UPDATE_QUEUE: str
    PAGE_CRAWL_MAX_DEPTH: int = 2
    PAGE_CRAWL_UNLIMITED: bool = False
    TEST_SUITE_EXECUTION_QUEUE: str
    TEST_SUITE_EXECUTION_QUEUE: str



    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()