import pytest
from httpx import AsyncClient

from conftest import INTERNAL_HEADERS, UnreachableTransport
from product_service.core.http import get_http_client
from product_service.main import app as product_app

pytestmark = pytest.mark.asyncio


async def test_admin_routes_authenticate_via_auth_service(
    product_client: AsyncClient,
    admin_token: str,
    customer_token: str,
):
    """product-service has no user table; it asks auth-service who the caller is."""
    admin_res = await product_client.get(
        "/products/low-stock", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_res.status_code == 200

    customer_res = await product_client.get(
        "/products/low-stock", headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert customer_res.status_code == 403


async def test_auth_service_down_returns_503(product_client: AsyncClient):
    async def broken_http():
        async with AsyncClient(transport=UnreachableTransport()) as http:
            yield http

    product_app.dependency_overrides[get_http_client] = broken_http
    res = await product_client.get(
        "/products/low-stock", headers={"Authorization": "Bearer some-token"}
    )
    assert res.status_code == 503


async def test_internal_endpoints_require_internal_key(product_client: AsyncClient, product_id: int):
    payload = {"items": [{"productId": product_id, "quantity": 1}]}

    no_key = await product_client.post("/internal/inventory/reserve", json=payload)
    assert no_key.status_code == 403

    wrong_key = await product_client.post(
        "/internal/inventory/reserve", json=payload, headers={"X-Internal-Key": "nope"}
    )
    assert wrong_key.status_code == 403


async def test_reserve_and_release_inventory(product_client: AsyncClient, product_id: int):
    payload = {"items": [{"productId": product_id, "quantity": 4}]}

    reserve = await product_client.post(
        "/internal/inventory/reserve", json=payload, headers=INTERNAL_HEADERS
    )
    assert reserve.status_code == 200
    assert reserve.json() == {
        "items": [{"product_id": product_id, "quantity": 4, "price_in_cents": 7500}]
    }
    assert (await product_client.get("/products")).json()[0]["quantity"] == 2

    release = await product_client.post(
        "/internal/inventory/release", json=payload, headers=INTERNAL_HEADERS
    )
    assert release.status_code == 204
    assert (await product_client.get("/products")).json()[0]["quantity"] == 6


async def test_reserve_reports_out_of_stock_as_conflict(product_client: AsyncClient, product_id: int):
    res = await product_client.post(
        "/internal/inventory/reserve",
        json={"items": [{"productId": product_id, "quantity": 100}]},
        headers=INTERNAL_HEADERS,
    )
    assert res.status_code == 409
    assert (await product_client.get("/products")).json()[0]["quantity"] == 6
