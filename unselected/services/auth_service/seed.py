import asyncio

from auth_service.core.database import AsyncSessionLocal
from auth_service.models import UserModel
from auth_service.service import hash_password


async def seed_data():
    async with AsyncSessionLocal() as db:
        async with db.begin():
            db.add_all([
                UserModel(name="Admin User", email="admin@ecom.com",
                          password_hash=hash_password("admin123"), role="admin"),
                UserModel(name="John Doe", email="john@ecom.com",
                          password_hash=hash_password("customer123"), role="customer"),
            ])
    print("auth-service database seeded with demo users!")


if __name__ == "__main__":
    asyncio.run(seed_data())
