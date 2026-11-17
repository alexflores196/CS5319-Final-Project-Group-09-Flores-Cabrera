from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from product_service.models import (
    InventoryItem,
    ProductCreate,
    ProductModel,
    ProductUpdate,
    ReservedItem,
)


class ProductNotFoundError(Exception):
    pass


class ProductOutOfStockError(Exception):
    pass


class ProductsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_active_products(self) -> List[ProductModel]:
        result = await self.db.execute(select(ProductModel).where(ProductModel.is_active == True))  # noqa: E712
        return result.scalars().all()

    async def list_low_stock(self, threshold: int) -> List[ProductModel]:
        result = await self.db.execute(select(ProductModel).where(ProductModel.quantity <= threshold))
        return result.scalars().all()

    async def get_product(self, product_id: int) -> Optional[ProductModel]:
        result = await self.db.execute(select(ProductModel).where(ProductModel.id == product_id))
        return result.scalar_one_or_none()

    async def create_product(self, payload: ProductCreate) -> ProductModel:
        new_product = ProductModel(
            name=payload.name,
            description=payload.description,
            image_url=payload.image_url,
            category=payload.category,
            price_in_cents=payload.price_in_cents,
            quantity=payload.quantity,
            is_active=True,
        )
        self.db.add(new_product)
        await self.db.commit()
        await self.db.refresh(new_product)
        return new_product

    async def update_product(self, product_id: int, payload: ProductUpdate) -> Optional[ProductModel]:
        product = await self.get_product(product_id)
        if not product:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, key, value)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def reserve_inventory(self, items: List[InventoryItem]) -> List[ReservedItem]:
        """Validate and deduct stock for every item atomically (all or nothing)."""
        reserved: List[ReservedItem] = []
        try:
            for item in items:
                result = await self.db.execute(
                    select(ProductModel).where(ProductModel.id == item.productId).with_for_update()
                )
                product = result.scalar_one_or_none()
                if not product:
                    raise ProductNotFoundError(f"Product with ID {item.productId} not found")
                if product.quantity < item.quantity:
                    raise ProductOutOfStockError(
                        f"Product '{product.name}' only has {product.quantity} units left"
                    )
                product.quantity -= item.quantity
                reserved.append(
                    ReservedItem(product_id=product.id, quantity=item.quantity, price_in_cents=product.price_in_cents)
                )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return reserved

    async def release_inventory(self, items: List[InventoryItem]) -> None:
        """Compensating action: return previously reserved stock."""
        for item in items:
            product = await self.get_product(item.productId)
            if product:
                product.quantity += item.quantity
        await self.db.commit()
