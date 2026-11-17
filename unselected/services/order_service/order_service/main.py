import logging
import sys

from fastapi import FastAPI, status
from fastapi.responses import PlainTextResponse

from order_service.core.config import settings
from order_service.router import router as orders_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - order-service - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

app = FastAPI(title="Ecommerce Order Service")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return PlainTextResponse("all good")


app.include_router(orders_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("order_service.main:app", host=settings.HOST, port=settings.PORT, reload=True)
