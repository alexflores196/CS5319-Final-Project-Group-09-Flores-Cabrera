import logging
import sys

from fastapi import FastAPI, status
from fastapi.responses import PlainTextResponse

from product_service.core.config import settings
from product_service.router import internal_router
from product_service.router import router as products_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - product-service - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

app = FastAPI(title="Ecommerce Product Service")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return PlainTextResponse("all good")


app.include_router(products_router)
app.include_router(internal_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("product_service.main:app", host=settings.HOST, port=settings.PORT, reload=True)
