from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.orders.models import CreateOrderParams, OrderItemModel, OrderModel
from app.modules.products.models import ProductModel


class ProductNotFoundError(Exception):
    pass


class ProductOutOfStockError(Exception):
    pass


class OrdersService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def place_order(self, temp_order: CreateOrderParams) -> OrderModel:
        if temp_order.customerId == 0:
            raise ValueError("customer ID is required")
        if not temp_order.items:
            raise ValueError("at least one item is required")

        # Atomic transaction block
        async with self.db.begin_nested():
            # 1. Create the base Order record
            new_order = OrderModel(customer_id=temp_order.customerId)
            self.db.add(new_order)
            await self.db.flush()

            for item in temp_order.items:
                # 2. Fetch the product using row locking if needed (select ... for update)
                result = await self.db.execute(
                    select(ProductModel).where(ProductModel.id == item.productId)
                )
                product = result.scalar_one_or_none()

                if not product:
                    raise ProductNotFoundError(f"Product with ID {item.productId} not found")

                # 3. Stock validation
                if product.quantity < item.quantity:
                    raise ProductOutOfStockError(
                        f"Product '{product.name}' only has {product.quantity} units left"
                    )

                # 4. DEDUCT INVENTORY IN DATABASE
                product.quantity -= item.quantity

                # 5. Create the Order Item record
                order_item = OrderItemModel(
                    order_id=new_order.id,
                    product_id=item.productId,
                    quantity=item.quantity,
                    price_cents=product.price_in_cents
                )
                self.db.add(order_item)

        # Commit transaction to persist both order items and updated product stock counts
        await self.db.commit()
        await self.db.refresh(new_order)
        return new_order