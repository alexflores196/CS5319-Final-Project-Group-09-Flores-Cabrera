from typing import List
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.modules.products.models import ProductResponse
from app.core.database import Base, ID_TYPE

class CartModel(Base):
    __tablename__ = "carts"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    items = relationship("CartItemModel", back_populates="cart", cascade="all, delete-orphan")

class CartItemModel(Base):
    __tablename__ = "cart_items"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    cart_id = Column(ID_TYPE, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(ID_TYPE, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cart = relationship("CartModel", back_populates="items")
    product = relationship("ProductModel")

    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="unique_cart_product"),)

# Pydantic Schemas
class CartItemResponse(BaseModel):
    id: int
    product: ProductResponse
    quantity: int
    subtotal_cents: int

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_cents: int

    class Config:
        from_attributes = True