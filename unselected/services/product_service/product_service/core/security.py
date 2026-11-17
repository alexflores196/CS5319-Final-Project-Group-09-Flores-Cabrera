import logging
from dataclasses import dataclass

import httpx
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from product_service.core.config import settings
from product_service.core.http import get_http_client

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass
class CurrentUser:
    id: int
    email: str
    role: str


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    http: httpx.AsyncClient = Depends(get_http_client),
) -> CurrentUser:
    """Resolve the bearer token by asking auth-service, which owns user data."""
    try:
        response = await http.get(
            f"{settings.AUTH_SERVICE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    except httpx.HTTPError as err:
        logger.error("auth-service unreachable: %s", err)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Auth service unavailable")

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    data = response.json()
    return CurrentUser(id=data["id"], email=data["email"], role=data["role"])


async def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have administrative privileges",
        )
    return current_user


async def require_internal_caller(x_internal_key: str = Header(default="")) -> None:
    """Guard for service-to-service endpoints; the gateway never routes /internal."""
    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Internal endpoint")
