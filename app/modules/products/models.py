from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text, func
from app.core.database import Base, ID_TYPE

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True, default="")
    category = Column(String(100), nullable=True, default="General")
    price_in_cents = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# Pydantic Schemas
class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    price_in_cents: int
    quantity: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: Optional[str] = "General"
    price_in_cents: int
    quantity: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price_in_cents: Optional[int] = None
    quantity: Optional[int] = None
    is_active: Optional[bool] = None