from datetime import datetime
from typing import List

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app.core.database import Base, ID_TYPE


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    customer_id = Column(ID_TYPE, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    items = relationship("OrderItemModel", back_populates="order")


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    order_id = Column(ID_TYPE, ForeignKey("orders.id"), nullable=False)
    product_id = Column(ID_TYPE, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)

    order = relationship("OrderModel", back_populates="items")


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