from typing import AsyncGenerator

import httpx

from order_service.core.config import settings


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client used for service-to-service calls (overridden in tests)."""
    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        yield client
