from typing import Any, Dict, List

import httpx

from order_service.core.config import settings


class ProductNotFoundError(Exception):
    pass


class ProductOutOfStockError(Exception):
    pass


class ProductServiceUnavailableError(Exception):
    pass


class ProductServiceClient:
    """Typed wrapper around product-service's internal inventory API."""

    def __init__(self, http: httpx.AsyncClient):
        self.http = http
        self.base_url = settings.PRODUCT_SERVICE_URL
        self.headers = {"X-Internal-Key": settings.INTERNAL_API_KEY}

    async def _post(self, path: str, items: List[Dict[str, int]]) -> httpx.Response:
        try:
            return await self.http.post(f"{self.base_url}{path}", json={"items": items}, headers=self.headers)
        except httpx.HTTPError as err:
            raise ProductServiceUnavailableError(f"Product service unavailable: {err}") from err

    async def reserve(self, items: List[Dict[str, int]]) -> List[Dict[str, Any]]:
        response = await self._post("/internal/inventory/reserve", items)
        detail = _detail(response)
        if response.status_code == 404:
            raise ProductNotFoundError(detail)
        if response.status_code == 409:
            raise ProductOutOfStockError(detail)
        if response.status_code != 200:
            raise ProductServiceUnavailableError(f"Product service error ({response.status_code}): {detail}")
        return response.json()["items"]

    async def release(self, items: List[Dict[str, int]]) -> None:
        response = await self._post("/internal/inventory/release", items)
        if response.status_code >= 400:
            raise ProductServiceUnavailableError(f"Inventory release failed ({response.status_code})")


def _detail(response: httpx.Response) -> str:
    try:
        return str(response.json().get("detail", response.text))
    except ValueError:
        return response.text
