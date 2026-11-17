"""End-to-end tests through the API gateway.

The first four tests are the same scenarios as Selected/tests/test_api.py,
which shows the microservices system keeps the monolith's public API.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_user_registration_and_login(client: AsyncClient):
    reg_res = await client.post(
        "/auth/register",
        json={
            "name": "Alex Flores",
            "email": "alex@test.com",
            "password": "securepassword123",
        },
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == "alex@test.com"
    assert reg_res.json()["role"] == "customer"

    dup_res = await client.post(
        "/auth/register",
        json={
            "name": "Alex Duplicate",
            "email": "alex@test.com",
            "password": "securepassword123",
        },
    )
    assert dup_res.status_code == 400

    login_res = await client.post(
        "/auth/login",
        json={
            "email": "alex@test.com",
            "password": "securepassword123",
        },
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_rbac_admin_product_creation(
    client: AsyncClient,
    customer_token: str,
    admin_token: str,
):
    product_payload = {
        "name": "Developer Mechanical Keyboard",
        "description": "Tactile switches",
        "category": "Peripherals",
        "price_in_cents": 12000,
        "quantity": 10,
    }

    unauth_res = await client.post("/products", json=product_payload)
    assert unauth_res.status_code == 401

    customer_res = await client.post(
        "/products",
        json=product_payload,
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert customer_res.status_code == 403

    admin_res = await client.post(
        "/products",
        json=product_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 201
    assert admin_res.json()["name"] == "Developer Mechanical Keyboard"


async def test_admin_can_update_product(
    client: AsyncClient,
    customer_token: str,
    admin_token: str,
):
    create_res = await client.post(
        "/products",
        json={
            "name": "Test Headphones",
            "description": "Original description",
            "category": "Audio",
            "price_in_cents": 10000,
            "quantity": 5,
            "image_url": "/static/images/products/wireless-headphones.jpg",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_res.status_code == 201
    product_id = create_res.json()["id"]

    update_payload = {
        "name": "Updated Test Headphones",
        "description": "Updated description",
        "category": "Audio",
        "price_in_cents": 12000,
        "quantity": 12,
        "image_url": "/static/images/products/curved-monitor.jpg",
    }

    unauth_res = await client.put(
        f"/products/{product_id}",
        json=update_payload,
    )
    assert unauth_res.status_code == 401

    customer_res = await client.put(
        f"/products/{product_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert customer_res.status_code == 403

    admin_res = await client.put(
        f"/products/{product_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200

    updated = admin_res.json()
    assert updated["name"] == "Updated Test Headphones"
    assert updated["description"] == "Updated description"
    assert updated["category"] == "Audio"
    assert updated["price_in_cents"] == 12000
    assert updated["quantity"] == 12
    assert updated["image_url"] == "/static/images/products/curved-monitor.jpg"


async def test_low_stock_alert_and_checkout_deduction(
    client: AsyncClient,
    customer_token: str,
    admin_token: str,
):
    create_res = await client.post(
        "/products",
        json={
            "name": "USB-C Dock",
            "description": "Multi-port hub",
            "category": "Accessories",
            "price_in_cents": 7500,
            "quantity": 6,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_res.status_code == 201
    product_id = create_res.json()["id"]

    low_stock_before = await client.get(
        "/products/low-stock?threshold=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert low_stock_before.status_code == 200
    assert len(low_stock_before.json()) == 0

    order_res = await client.post(
        "/order",
        json={
            "customerId": 1,
            "items": [{"productId": product_id, "quantity": 2}],
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert order_res.status_code in (200, 201)

    low_stock_after = await client.get(
        "/products/low-stock?threshold=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert low_stock_after.status_code == 200
    items = low_stock_after.json()
    assert len(items) == 1
    assert items[0]["id"] == product_id
    assert items[0]["quantity"] == 4

async def test_list_products_is_public_and_hides_inactive(
    client: AsyncClient,
    admin_token: str,
    product_id: int,
):
    list_res = await client.get("/products")
    assert list_res.status_code == 200
    assert [p["id"] for p in list_res.json()] == [product_id]

    await client.put(
        f"/products/{product_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    list_after = await client.get("/products")
    assert list_after.json() == []


async def test_update_missing_product_returns_404(client: AsyncClient, admin_token: str):
    res = await client.put(
        "/products/9999",
        json={"name": "Ghost"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Product not found"


async def test_invalid_token_is_rejected(client: AsyncClient):
    res = await client.get(
        "/products/low-stock",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert res.status_code == 401


async def test_checkout_out_of_stock_is_rejected_without_deduction(
    client: AsyncClient,
    admin_token: str,
    product_id: int,
):
    order_res = await client.post(
        "/order",
        json={"customerId": 1, "items": [{"productId": product_id, "quantity": 7}]},
    )
    assert order_res.status_code == 400
    assert "only has 6 units left" in order_res.json()["detail"]

    products = (await client.get("/products")).json()
    assert products[0]["quantity"] == 6


async def test_checkout_is_all_or_nothing_across_items(
    client: AsyncClient,
    admin_token: str,
    product_id: int,
):
    order_res = await client.post(
        "/order",
        json={
            "customerId": 1,
            "items": [
                {"productId": product_id, "quantity": 2},
                {"productId": 9999, "quantity": 1},
            ],
        },
    )
    assert order_res.status_code == 404
    assert order_res.json()["detail"] == "Product with ID 9999 not found"

    products = (await client.get("/products")).json()
    assert products[0]["quantity"] == 6


async def test_checkout_validation_errors(client: AsyncClient, product_id: int):
    missing_customer = await client.post(
        "/order",
        json={"customerId": 0, "items": [{"productId": product_id, "quantity": 1}]},
    )
    assert missing_customer.status_code == 400
    assert missing_customer.json()["detail"] == "customer ID is required"

    no_items = await client.post("/order", json={"customerId": 1, "items": []})
    assert no_items.status_code == 400
    assert no_items.json()["detail"] == "at least one item is required"
