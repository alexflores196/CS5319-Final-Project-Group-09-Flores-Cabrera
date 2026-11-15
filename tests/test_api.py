import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_user_registration_and_login(client: AsyncClient):
    # 1. Register a new user
    reg_res = await client.post("/auth/register", json={
        "name": "Alex Flores",
        "email": "alex@test.com",
        "password": "securepassword123"
    })
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == "alex@test.com"
    assert reg_res.json()["role"] == "customer"

    # 2. Prevent duplicate email registration
    dup_res = await client.post("/auth/register", json={
        "name": "Alex Duplicate",
        "email": "alex@test.com",
        "password": "securepassword123"
    })
    assert dup_res.status_code == 400

    # 3. Verify login returns a Bearer JWT
    login_res = await client.post("/auth/login", json={
        "email": "alex@test.com",
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_rbac_admin_product_creation(client: AsyncClient, customer_token: str, admin_token: str):
    product_payload = {
        "name": "Developer Mechanical Keyboard",
        "description": "Tactile switches",
        "category": "Peripherals",
        "price_in_cents": 12000,
        "quantity": 10
    }

    # 1. Unauthenticated request must fail (401)
    unauth_res = await client.post("/products", json=product_payload)
    assert unauth_res.status_code == 401

    # 2. Standard customer request must fail (403 Forbidden)
    cust_res = await client.post(
        "/products",
        json=product_payload,
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert cust_res.status_code == 403

    # 3. Admin request must succeed (201 Created)
    admin_res = await client.post(
        "/products",
        json=product_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_res.status_code == 201
    assert admin_res.json()["name"] == "Developer Mechanical Keyboard"

async def test_low_stock_alert_and_checkout_deduction(client: AsyncClient, customer_token: str, admin_token: str):
    # 1. Admin creates a product with stock = 6
    create_res = await client.post(
        "/products",
        json={
            "name": "USB-C Dock",
            "description": "Multi-port hub",
            "category": "Accessories",
            "price_in_cents": 7500,
            "quantity": 6
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    product_id = create_res.json()["id"]

    # 2. Low-stock endpoint (threshold=5) should initially be empty
    low_stock_before = await client.get(
        "/products/low-stock?threshold=5",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert low_stock_before.status_code == 200
    assert len(low_stock_before.json()) == 0

    # 3. Customer places an order for 2 units (reducing stock from 6 -> 4)
    order_res = await client.post(
        "/order",
        json={
            "customerId": 1,
            "items": [{"productId": product_id, "quantity": 2}]
        },
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert order_res.status_code in (200, 201)

    # 4. Verify low-stock endpoint now flags the product (4 <= 5)
    low_stock_after = await client.get(
        "/products/low-stock?threshold=5",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    items = low_stock_after.json()
    assert len(items) == 1
    assert items[0]["id"] == product_id
    assert items[0]["quantity"] == 4