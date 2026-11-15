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