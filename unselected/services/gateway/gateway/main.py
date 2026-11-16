import logging
import os
import sys

import httpx
from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from gateway.config import settings
from gateway.proxy import forward, get_http_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - gateway - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ecom_gateway")

app = FastAPI(title="Ecommerce API Gateway")

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

PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return PlainTextResponse("Frontend index.html not found in /static", status_code=404)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return PlainTextResponse("all good")


@app.get("/health/services")
async def services_health(http: httpx.AsyncClient = Depends(get_http_client)):
    """Report the health of every downstream service."""
    services = {
        "auth-service": settings.AUTH_SERVICE_URL,
        "product-service": settings.PRODUCT_SERVICE_URL,
        "order-service": settings.ORDER_SERVICE_URL,
    }
    report = {}
    for name, base_url in services.items():
        try:
            res = await http.get(f"{base_url}/health")
            report[name] = "up" if res.status_code == 200 else f"error ({res.status_code})"
        except httpx.HTTPError:
            report[name] = "down"
    healthy = all(v == "up" for v in report.values())
    return JSONResponse(status_code=200 if healthy else 503, content=report)


# --- Routing table: public path prefix -> owning service -------------------

@app.api_route("/auth/{path:path}", methods=PROXY_METHODS, tags=["Authentication"])
async def auth_proxy(request: Request, http: httpx.AsyncClient = Depends(get_http_client)):
    return await forward(request, settings.AUTH_SERVICE_URL, http)


@app.api_route("/products", methods=PROXY_METHODS, tags=["Products"])
@app.api_route("/products/{path:path}", methods=PROXY_METHODS, tags=["Products"])
async def products_proxy(request: Request, http: httpx.AsyncClient = Depends(get_http_client)):
    return await forward(request, settings.PRODUCT_SERVICE_URL, http)


@app.api_route("/order", methods=PROXY_METHODS, tags=["Orders"])
async def orders_proxy(request: Request, http: httpx.AsyncClient = Depends(get_http_client)):
    return await forward(request, settings.ORDER_SERVICE_URL, http)


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Gateway starting at http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("gateway.main:app", host=settings.HOST, port=settings.PORT, reload=True)
