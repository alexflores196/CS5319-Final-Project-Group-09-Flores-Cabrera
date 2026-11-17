import asyncio

from product_service.core.database import AsyncSessionLocal
from product_service.models import ProductModel


async def seed_data():
    async with AsyncSessionLocal() as db:
        async with db.begin():
            db.add_all([
                ProductModel(
                    name="Minimalist Wireless Headphones",
                    description="High-fidelity Bluetooth headphones with active noise cancellation.",
                    category="Audio",
                    price_in_cents=14999,
                    quantity=15,
                    is_active=True,
                    image_url="/static/images/products/wireless-headphones.jpg",
                ),
                ProductModel(
                    name="Ergonomic Mechanical Keyboard",
                    description="RGB customizable mechanical keyboard with tactile switches.",
                    category="Peripherals",
                    price_in_cents=12950,
                    quantity=8,
                    is_active=True,
                    image_url="/static/images/products/wireless-keyboard.jpg",
                ),
                ProductModel(
                    name="Ultra-Wide Curved Monitor 34\"",
                    description="34-inch 144Hz curved gaming and productivity monitor.",
                    category="Displays",
                    price_in_cents=49999,
                    quantity=4,
                    is_active=True,
                    image_url="/static/images/products/curved-monitor.jpg",
                ),
                ProductModel(
                    name="Precision Optical Mouse",
                    description="High DPI ergonomic wired mouse for gaming and design.",
                    category="Peripherals",
                    price_in_cents=4500,
                    quantity=25,
                    is_active=True,
                    image_url="/static/images/products/optical-mouse.jpg",
                ),
            ])
    print("product-service database seeded with demo products!")


if __name__ == "__main__":
    asyncio.run(seed_data())
