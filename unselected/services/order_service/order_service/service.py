import logging

from sqlalchemy.ext.asyncio import AsyncSession

from order_service.clients import ProductServiceClient
from order_service.models import CreateOrderParams, OrderItemModel, OrderModel

logger = logging.getLogger(__name__)


class OrdersService:
    def __init__(self, db: AsyncSession, products: ProductServiceClient):
        self.db = db
        self.products = products

    async def place_order(self, temp_order: CreateOrderParams) -> OrderModel:
        if temp_order.customerId == 0:
            raise ValueError("customer ID is required")
        if not temp_order.items:
            raise ValueError("at least one item is required")

        requested = [{"productId": i.productId, "quantity": i.quantity} for i in temp_order.items]

        # Step 1 (saga): product-service validates and deducts stock atomically,
        # returning the price of each item at the time of purchase.
        reserved = await self.products.reserve(requested)

        # Step 2 (saga): persist the order locally. If this fails, compensate by
        # returning the stock to product-service.
        try:
            new_order = OrderModel(customer_id=temp_order.customerId)
            self.db.add(new_order)
            await self.db.flush()
            for item in reserved:
                self.db.add(
                    OrderItemModel(
                        order_id=new_order.id,
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                        price_cents=item["price_in_cents"],
                    )
                )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to save order; releasing reserved inventory")
            await self.products.release(requested)
            raise

        await self.db.refresh(new_order)
        return new_order
