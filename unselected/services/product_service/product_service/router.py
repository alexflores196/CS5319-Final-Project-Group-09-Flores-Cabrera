import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from product_service.core.database import get_db
from product_service.core.security import CurrentUser, require_admin, require_internal_caller
from product_service.models import (
    InventoryRequest,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ReservationResponse,
)
from product_service.service import ProductNotFoundError, ProductOutOfStockError, ProductsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])
internal_router = APIRouter(
    prefix="/internal/inventory",
    tags=["Internal"],
    dependencies=[Depends(require_internal_caller)],
)


@router.get("", response_model=List[ProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    return await ProductsService(db).list_active_products()


@router.get("/low-stock", response_model=List[ProductResponse])
async def get_low_stock_products(
    threshold: int = 5,
    db: AsyncSession = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """Admin endpoint to identify products with low stock (Requirement 2.1)"""
    return await ProductsService(db).list_low_stock(threshold)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """Admin endpoint to create a new product (Requirement 2.1)"""
    return await ProductsService(db).create_product(payload)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """Admin endpoint to update product info, price, or inventory (Requirement 2.1)"""
    product = await ProductsService(db).update_product(product_id, payload)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@internal_router.post("/reserve", response_model=ReservationResponse)
async def reserve_inventory(payload: InventoryRequest, db: AsyncSession = Depends(get_db)):
    """Called by order-service: check stock and deduct it for all items atomically."""
    try:
        reserved = await ProductsService(db).reserve_inventory(payload.items)
    except ProductNotFoundError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except ProductOutOfStockError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    return {"items": reserved}


@internal_router.post("/release", status_code=status.HTTP_204_NO_CONTENT)
async def release_inventory(payload: InventoryRequest, db: AsyncSession = Depends(get_db)):
    """Called by order-service to compensate a reservation when the order cannot be saved."""
    await ProductsService(db).release_inventory(payload.items)
