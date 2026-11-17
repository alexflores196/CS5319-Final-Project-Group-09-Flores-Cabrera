import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import UnreachableTransport
from order_service.core.http import get_http_client
from order_service.main import app as order_app
from order_service.models import CreateOrderParams, OrderItemModel, OrderModel
from order_service.service import OrdersService

pytestmark = pytest.mark.asyncio


async def test_order_records_price_from_product_service(
    order_client: AsyncClient,
    order_session: AsyncSession,
    product_id: int,
):
    res = await order_client.post(
        "/order",
        json={"customerId": 1, "items": [{"productId": product_id, "quantity": 2}]},
    )
    assert res.status_code == 201
    assert res.json()["customer_id"] == 1

    items = (await order_session.execute(select(OrderItemModel))).scalars().all()
    assert len(items) == 1
    assert items[0].product_id == product_id
    assert items[0].quantity == 2
    assert items[0].price_cents == 7500


async def test_product_service_down_returns_503(order_client: AsyncClient):
    async def broken_http():
        async with AsyncClient(transport=UnreachableTransport()) as http:
            yield http

    order_app.dependency_overrides[get_http_client] = broken_http
    res = await order_client.post(
        "/order", json={"customerId": 1, "items": [{"productId": 1, "quantity": 1}]}
    )
    assert res.status_code == 503


class FakeProductClient:
    def __init__(self):
        self.released = None

    async def reserve(self, items):
        return [{"product_id": i["productId"], "quantity": i["quantity"], "price_in_cents": 100} for i in items]

    async def release(self, items):
        self.released = items


async def test_failed_order_save_releases_reserved_stock(order_session: AsyncSession, monkeypatch):
    """Saga compensation: if the order can't be stored, stock goes back to product-service."""
    products = FakeProductClient()

    async def failing_commit():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(order_session, "commit", failing_commit)

    params = CreateOrderParams(customerId=1, items=[{"productId": 5, "quantity": 3}])
    with pytest.raises(RuntimeError):
        await OrdersService(order_session, products).place_order(params)

    assert products.released == [{"productId": 5, "quantity": 3}]
    orders = (await order_session.execute(select(OrderModel))).scalars().all()
    assert orders == []
