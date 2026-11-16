import logging
import sys

from fastapi import FastAPI, status
from fastapi.responses import PlainTextResponse

from auth_service.core.config import settings
from auth_service.router import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - auth-service - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

app = FastAPI(title="Ecommerce Auth Service")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return PlainTextResponse("all good")


app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("auth_service.main:app", host=settings.HOST, port=settings.PORT, reload=True)
