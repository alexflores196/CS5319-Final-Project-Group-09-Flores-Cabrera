import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from order_service.clients import (
    ProductNotFoundError,
    ProductOutOfStockError,
    ProductServiceClient,
    ProductServiceUnavailableError,
)
from order_service.core.database import get_db
from order_service.core.http import get_http_client
from order_service.models import CreateOrderParams, OrderResponse
from order_service.service import OrdersService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Orders"])


@router.post("/order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: CreateOrderParams,
    db: AsyncSession = Depends(get_db),
    http: httpx.AsyncClient = Depends(get_http_client),
):
    service = OrdersService(db, ProductServiceClient(http))
    try:
        return await service.place_order(payload)
    except ValueError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except ProductNotFoundError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except ProductOutOfStockError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except ProductServiceUnavailableError as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))
