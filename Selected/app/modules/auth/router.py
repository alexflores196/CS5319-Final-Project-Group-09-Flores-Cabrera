from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.service import AuthService
from app.modules.users.models import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterPayload(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "customer"

class LoginPayload(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterPayload, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register_user(payload.name, payload.email, payload.password, payload.role)
    return user

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginPayload, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token = await service.authenticate_user(payload.email, payload.password)
    return {"access_token": token, "token_type": "bearer"}