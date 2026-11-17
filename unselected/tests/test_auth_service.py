import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_and_login_directly(auth_client: AsyncClient):
    reg_res = await auth_client.post(
        "/auth/register",
        json={"name": "Direct User", "email": "direct@test.com", "password": "pw123456"},
    )
    assert reg_res.status_code == 201
    assert "password_hash" not in reg_res.json()

    bad_login = await auth_client.post(
        "/auth/login",
        json={"email": "direct@test.com", "password": "wrong"},
    )
    assert bad_login.status_code == 401

    unknown_login = await auth_client.post(
        "/auth/login",
        json={"email": "nobody@test.com", "password": "pw123456"},
    )
    assert unknown_login.status_code == 401


async def test_me_resolves_token_to_user(auth_client: AsyncClient, admin_token: str):
    """GET /auth/me is the contract other services use to authenticate callers."""
    res = await auth_client.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "admin@test.com"
    assert body["role"] == "admin"


async def test_me_rejects_missing_or_invalid_token(auth_client: AsyncClient):
    missing = await auth_client.get("/auth/me")
    assert missing.status_code == 401

    invalid = await auth_client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert invalid.status_code == 401


async def test_health(auth_client: AsyncClient):
    res = await auth_client.get("/health")
    assert res.status_code == 200
    assert res.text == "all good"
