from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.products.models import ProductModel

class ProductsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_products(self) -> List[ProductModel]:
        result = await self.db.execute(select(ProductModel))
        return result.scalars().all()