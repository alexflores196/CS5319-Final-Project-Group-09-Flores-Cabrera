import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    GOOSE_DBSTRING: str = os.getenv(
        "GOOSE_DBSTRING",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ecom"
    )

    class Config:
        env_file = ".env"


settings = Settings()