"""
Test harness for the microservices architecture.

Every service runs in-process against its own isolated in-memory SQLite
database (mirroring database-per-service). Service-to-service HTTP calls are
routed through `httpx.ASGITransport`, so the gateway -> service and
service -> service hops are exercised exactly as in production, just without
a network.
"""
import bcrypt
import httpx
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from auth_service.core import database as auth_db
from auth_service.main import app as auth_app
from auth_service.models import UserModel
from gateway.config import settings as gateway_settings
from gateway.main import app as gateway_app
from gateway.proxy import get_http_client as gateway_http
from order_service.core import database as order_db
from order_service.core.http import get_http_client as order_http
from order_service.main import app as order_app
from order_service.models import OrderModel, OrderItemModel, CartModel, CartItemModel  # noqa: F401
from product_service.core import database as product_db
from product_service.core.config import settings as product_settings
from product_service.core.http import get_http_client as product_http
from product_service.main import app as product_app
from product_service.models import ProductModel  # noqa: F401

# Use an isolated in-memory SQLite database per service for testing.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

SERVICE_DATABASES = {
    "auth": auth_db,
    "product": product_db,
    "order": order_db,
}

ALL_APPS = (auth_app, product_app, order_app, gateway_app)

INTERNAL_HEADERS = {"X-Internal-Key": product_settings.INTERNAL_API_KEY}


def _make_session_factory():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=StaticPool)
    return engine, async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_sessions():
    """Create fresh tables in every service database and drop them afterward."""
    engines, sessions = {}, {}
    for name, module in SERVICE_DATABASES.items():
        engine, factory = _make_session_factory()
        async with engine.begin() as conn:
            await conn.run_sync(module.Base.metadata.create_all)
        engines[name] = engine
        sessions[name] = factory()

    yield sessions

    for name, module in SERVICE_DATABASES.items():
        await sessions[name].close()
        async with engines[name].begin() as conn:
            await conn.run_sync(module.Base.metadata.drop_all)
        await engines[name].dispose()


@pytest_asyncio.fixture
async def auth_session(db_sessions) -> AsyncSession:
    return db_sessions["auth"]


@pytest_asyncio.fixture
async def product_session(db_sessions) -> AsyncSession:
    return db_sessions["product"]


@pytest_asyncio.fixture
async def order_session(db_sessions) -> AsyncSession:
    return db_sessions["order"]


@pytest_asyncio.fixture(scope="function")
async def service_mesh(db_sessions):
    """
    Wire every service to its test database and to each other.

    A single httpx client mounts each service's base URL onto that service's
    ASGI app, standing in for the Docker network.
    """
    mesh = AsyncClient(
        mounts={
            gateway_settings.AUTH_SERVICE_URL: ASGITransport(app=auth_app),
            gateway_settings.PRODUCT_SERVICE_URL: ASGITransport(app=product_app),
            gateway_settings.ORDER_SERVICE_URL: ASGITransport(app=order_app),
        }
    )

    def session_override(session):
        async def override_get_db():
            yield session
        return override_get_db

    async def override_http():
        yield mesh

    auth_app.dependency_overrides[auth_db.get_db] = session_override(db_sessions["auth"])
    product_app.dependency_overrides[product_db.get_db] = session_override(db_sessions["product"])
    order_app.dependency_overrides[order_db.get_db] = session_override(db_sessions["order"])
    product_app.dependency_overrides[product_http] = override_http
    order_app.dependency_overrides[order_http] = override_http
    gateway_app.dependency_overrides[gateway_http] = override_http

    yield mesh

    await mesh.aclose()
    for app in ALL_APPS:
        app.dependency_overrides.clear()


def _client_for(app) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest_asyncio.fixture(scope="function")
async def client(service_mesh):
    """AsyncClient talking to the API gateway: the system's public entry point."""
    async with _client_for(gateway_app) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def auth_client(service_mesh):
    """AsyncClient talking directly to auth-service (bypassing the gateway)."""
    async with _client_for(auth_app) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def product_client(service_mesh):
    """AsyncClient talking directly to product-service (bypassing the gateway)."""
    async with _client_for(product_app) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def order_client(service_mesh):
    """AsyncClient talking directly to order-service (bypassing the gateway)."""
    async with _client_for(order_app) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, auth_session: AsyncSession) -> str:
    """Seed an admin user in auth-service's database and return a valid JWT."""
    pwd_hash = bcrypt.hashpw(b"adminpass", bcrypt.gensalt()).decode("utf-8")

    admin = UserModel(name="Test Admin", email="admin@test.com", password_hash=pwd_hash, role="admin")
    auth_session.add(admin)
    await auth_session.commit()

    response = await client.post("/auth/login", json={"email": "admin@test.com", "password": "adminpass"})
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def customer_token(client: AsyncClient) -> str:
    """Register a customer via the gateway and return a valid JWT."""
    await client.post(
        "/auth/register",
        json={"name": "Test Customer", "email": "customer@test.com", "password": "customerpass"},
    )
    response = await client.post(
        "/auth/login",
        json={"email": "customer@test.com", "password": "customerpass"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def product_id(client: AsyncClient, admin_token: str) -> int:
    """Create a product with 6 units in stock and return its id."""
    response = await client.post(
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
    assert response.status_code == 201
    return response.json()["id"]


class UnreachableTransport(httpx.AsyncBaseTransport):
    """Transport that simulates a downstream service being down."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)
