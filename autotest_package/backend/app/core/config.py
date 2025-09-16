import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change_me")
    ADMIN_USERNAME: str = os.getenv("USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("PASSWORD", "Admin@123")
    ADMIN_NAME: str = os.getenv("NAME", "Admin User")
    ADMIN_EMAIL: str = os.getenv("EMAIL", "admin@example.com")

settings = Settings()
