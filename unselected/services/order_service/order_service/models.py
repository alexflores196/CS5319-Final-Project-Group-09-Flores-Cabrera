from datetime import datetime
from typing import List

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship

from order_service.core.database import Base, ID_TYPE


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    # Reference to a user owned by auth-service (no cross-database foreign key).
    customer_id = Column(ID_TYPE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    items = relationship("OrderItemModel", back_populates="order")


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    order_id = Column(ID_TYPE, ForeignKey("orders.id"), nullable=False)
    # Reference to a product owned by product-service (no cross-database foreign key).
    product_id = Column(ID_TYPE, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)

    order = relationship("OrderModel", back_populates="items")


class CartModel(Base):
    """Persistent cart, kept with orders because checkout is the cart's consumer."""

    __tablename__ = "carts"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    items = relationship("CartItemModel", back_populates="cart", cascade="all, delete-orphan")


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    cart_id = Column(ID_TYPE, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(ID_TYPE, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cart = relationship("CartModel", back_populates="items")

    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="unique_cart_product"),)


# Pydantic Schemas
class OrderItemPayload(BaseModel):
    productId: int = Field(..., alias="productId")
    quantity: int

    class Config:
        populate_by_name = True


class CreateOrderParams(BaseModel):
    customerId: int = Field(..., alias="customerId")
    items: List[OrderItemPayload]

    class Config:
        populate_by_name = True


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    created_at: datetime

    class Config:
        from_attributes = True
