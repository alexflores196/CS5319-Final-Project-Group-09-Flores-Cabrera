import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8001
    HOST: str = "0.0.0.0"

    # Each service owns its own database (database-per-service pattern).
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5433/auth_db",
    )

    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    class Config:
        env_file = ".env"


settings = Settings()
