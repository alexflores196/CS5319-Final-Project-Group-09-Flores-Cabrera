import asyncio
import bcrypt
from app.core.database import AsyncSessionLocal
from app.modules.products.models import ProductModel
from app.modules.users.models import UserModel

async def seed_data():
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # Hash passwords directly using bcrypt (safely encoded and truncated to 72 bytes)
            admin_pwd_bytes = "admin123".encode('utf-8')[:72]
            customer_pwd_bytes = "customer123".encode('utf-8')[:72]

            admin_hash = bcrypt.hashpw(admin_pwd_bytes, bcrypt.gensalt()).decode('utf-8')
            customer_hash = bcrypt.hashpw(customer_pwd_bytes, bcrypt.gensalt()).decode('utf-8')

            admin_user = UserModel(
                name="Admin User",
                email="admin@ecom.com",
                password_hash=admin_hash,
                role="admin"
            )
            customer_user = UserModel(
                name="John Doe",
                email="john@ecom.com",
                password_hash=customer_hash,
                role="customer"
            )
            db.add_all([admin_user, customer_user])

            # Seed Products with Extended Fields
            sample_products = [
                ProductModel(
                    name="Minimalist Wireless Headphones",
                    description="High-fidelity Bluetooth headphones with active noise cancellation.",
                    category="Audio",
                    price_in_cents=14999,
                    quantity=15,
                    is_active=True
                ),
                ProductModel(
                    name="Ergonomic Mechanical Keyboard",
                    description="RGB customizable mechanical keyboard with tactile switches.",
                    category="Peripherals",
                    price_in_cents=12950,
                    quantity=8,
                    is_active=True
                ),
                ProductModel(
                    name="Ultra-Wide Curved Monitor 34\"",
                    description="34-inch 144Hz curved gaming and productivity monitor.",
                    category="Displays",
                    price_in_cents=49999,
                    quantity=4,
                    is_active=True
                ),
                ProductModel(
                    name="Precision Optical Mouse",
                    description="High DPI ergonomic wired mouse for gaming and design.",
                    category="Peripherals",
                    price_in_cents=4500,
                    quantity=25,
                    is_active=True
                )
            ]
            db.add_all(sample_products)

        await db.commit()
        print("Database successfully seeded with Users and Extended Products!")

if __name__ == "__main__":
    asyncio.run(seed_data())