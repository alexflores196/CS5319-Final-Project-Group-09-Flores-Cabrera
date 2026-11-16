import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8002
    HOST: str = "0.0.0.0"

    # Each service owns its own database (database-per-service pattern).
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5434/products_db",
    )

    # Downstream service used to resolve bearer tokens into users.
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    # Shared secret that internal (service-to-service) endpoints require.
    INTERNAL_API_KEY: str = "dev-internal-key-change-in-production"
    HTTP_TIMEOUT_SECONDS: float = 5.0

    class Config:
        env_file = ".env"


settings = Settings()
