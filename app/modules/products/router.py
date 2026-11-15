from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.modules.users.models import UserModel
from app.modules.products.models import ProductModel, ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[ProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductModel).where(ProductModel.is_active == True))
    return result.scalars().all()


@router.get("/low-stock", response_model=List[ProductResponse])
async def get_low_stock_products(
        threshold: int = 5,
        db: AsyncSession = Depends(get_db),
        admin: UserModel = Depends(require_admin)
):
    """Admin endpoint to identify products with low stock (Requirement 2.1)"""
    result = await db.execute(select(ProductModel).where(ProductModel.quantity <= threshold))
    return result.scalars().all()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
        payload: ProductCreate,
        db: AsyncSession = Depends(get_db),
        admin: UserModel = Depends(require_admin)
):
    """Admin endpoint to create a new product (Requirement 2.1)"""
    new_product = ProductModel(
        name=payload.name,
        description=payload.description,
        image_url=payload.image_url,
        category=payload.category,
        price_in_cents=payload.price_in_cents,
        quantity=payload.quantity,
        is_active=True
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
        product_id: int,
        payload: ProductUpdate,
        db: AsyncSession = Depends(get_db),
        admin: UserModel = Depends(require_admin)
):
    """Admin endpoint to update product info, price, or inventory (Requirement 2.1)"""
    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)
    return product