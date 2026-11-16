from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    AUTH_SERVICE_URL: str = "http://localhost:8001"
    PRODUCT_SERVICE_URL: str = "http://localhost:8002"
    ORDER_SERVICE_URL: str = "http://localhost:8003"
    HTTP_TIMEOUT_SECONDS: float = 10.0

    class Config:
        env_file = ".env"


settings = Settings()
