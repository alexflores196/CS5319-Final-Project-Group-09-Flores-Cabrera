import logging
from typing import AsyncGenerator

import httpx
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from gateway.config import settings

logger = logging.getLogger(__name__)

# Headers that describe a single connection and must not be forwarded.
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client used to reach downstream services (overridden in tests)."""
    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        yield client


def _filter_headers(headers) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}


async def forward(request: Request, base_url: str, http: httpx.AsyncClient) -> Response:
    """Forward the incoming request unchanged to `base_url` and relay the response."""
    url = f"{base_url}{request.url.path}"
    try:
        upstream = await http.request(
            request.method,
            url,
            params=request.query_params,
            headers=_filter_headers(request.headers),
            content=await request.body(),
        )
    except httpx.HTTPError as err:
        logger.error("Upstream %s unreachable: %s", base_url, err)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Upstream service unavailable"},
        )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=_filter_headers(upstream.headers),
    )
