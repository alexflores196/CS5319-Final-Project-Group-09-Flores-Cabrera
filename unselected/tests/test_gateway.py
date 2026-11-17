import pytest
from httpx import AsyncClient

from conftest import UnreachableTransport
from gateway.main import app as gateway_app
from gateway.proxy import get_http_client

pytestmark = pytest.mark.asyncio


async def test_gateway_serves_frontend_and_health(client: AsyncClient):
    home = await client.get("/")
    assert home.status_code == 200
    assert "text/html" in home.headers["content-type"]

    image = await client.get("/static/images/products/wireless-headphones.jpg")
    assert image.status_code == 200

    health = await client.get("/health")
    assert health.status_code == 200
    assert health.text == "all good"


async def test_gateway_reports_downstream_health(client: AsyncClient):
    res = await client.get("/health/services")
    assert res.status_code == 200
    assert res.json() == {
        "auth-service": "up",
        "product-service": "up",
        "order-service": "up",
    }


async def test_gateway_forwards_query_params(client: AsyncClient, admin_token: str, product_id: int):
    headers = {"Authorization": f"Bearer {admin_token}"}
    at_six = await client.get("/products/low-stock?threshold=6", headers=headers)
    assert [p["id"] for p in at_six.json()] == [product_id]

    at_five = await client.get("/products/low-stock?threshold=5", headers=headers)
    assert at_five.json() == []


async def test_gateway_does_not_expose_internal_endpoints(client: AsyncClient):
    res = await client.post("/internal/inventory/reserve", json={"items": []})
    assert res.status_code == 404


async def test_gateway_returns_503_when_service_is_down(client: AsyncClient):
    async def broken_http():
        async with AsyncClient(transport=UnreachableTransport()) as http:
            yield http

    gateway_app.dependency_overrides[get_http_client] = broken_http
    res = await client.get("/products")
    assert res.status_code == 503
    assert res.json()["detail"] == "Upstream service unavailable"
