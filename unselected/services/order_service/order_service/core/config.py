import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8003
    HOST: str = "0.0.0.0"

    # Each service owns its own database (database-per-service pattern).
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5435/orders_db",
    )

    # Downstream service that owns product inventory.
    PRODUCT_SERVICE_URL: str = "http://localhost:8002"
    # Shared secret sent when calling internal (service-to-service) endpoints.
    INTERNAL_API_KEY: str = "dev-internal-key-change-in-production"
    HTTP_TIMEOUT_SECONDS: float = 5.0

    class Config:
        env_file = ".env"


settings = Settings()
