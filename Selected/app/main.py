import logging
import os
import sys
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.modules.orders.router import router as orders_router
from app.modules.products.router import router as products_router
from app.modules.auth.router import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ecom_api")

app = FastAPI(title="Ecommerce Modular Monolith API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return PlainTextResponse("Frontend index.html not found in /static", status_code=404)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return PlainTextResponse("all good")

app.include_router(products_router)
app.include_router(orders_router)
app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Server starting at http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)