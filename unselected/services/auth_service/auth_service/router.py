from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.database import get_db
from auth_service.core.security import get_current_user
from auth_service.models import LoginPayload, RegisterPayload, TokenResponse, UserModel, UserResponse
from auth_service.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterPayload, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register_user(payload.name, payload.email, payload.password, payload.role)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginPayload, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token = await service.authenticate_user(payload.email, payload.password)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserModel = Depends(get_current_user)):
    """Token introspection used by other services to resolve the caller and their role."""
    return current_user
