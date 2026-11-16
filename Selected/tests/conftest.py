import bcrypt
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_db
from app.modules.users.models import UserModel  # noqa: F401
from app.modules.products.models import ProductModel  # noqa: F401
from app.modules.orders.models import OrderModel, OrderItemModel  # noqa: F401
from app.modules.cart.models import CartModel, CartItemModel  # noqa: F401
from app.main import app


# Use an isolated in-memory SQLite database for testing.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create fresh tables for each test and drop them afterward."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Provide an AsyncClient wired to the isolated test database."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(
    client: AsyncClient,
    db_session: AsyncSession,
) -> str:
    """Seed an admin user and return a valid JWT."""
    pwd_hash = bcrypt.hashpw(
        b"adminpass",
        bcrypt.gensalt(),
    ).decode("utf-8")

    admin = UserModel(
        name="Test Admin",
        email="admin@test.com",
        password_hash=pwd_hash,
        role="admin",
    )
    db_session.add(admin)
    await db_session.commit()

    response = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "adminpass",
        },
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def customer_token(client: AsyncClient) -> str:
    """Register a customer via the API and return a valid JWT."""
    await client.post(
        "/auth/register",
        json={
            "name": "Test Customer",
            "email": "customer@test.com",
            "password": "customerpass",
        },
    )

    response = await client.post(
        "/auth/login",
        json={
            "email": "customer@test.com",
            "password": "customerpass",
        },
    )
    return response.json()["access_token"]