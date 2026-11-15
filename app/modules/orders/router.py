import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.orders.models import CreateOrderParams, OrderResponse
from app.modules.orders.service import OrdersService, ProductNotFoundError, ProductOutOfStockError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Orders"])

@router.post("/order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: CreateOrderParams,
    db: AsyncSession = Depends(get_db)
):
    service = OrdersService(db)
    try:
        created_order = await service.place_order(payload)
        return created_order
    except ValueError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except ProductNotFoundError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except ProductOutOfStockError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))