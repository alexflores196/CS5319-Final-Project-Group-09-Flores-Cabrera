from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.config import settings
from auth_service.models import UserModel


def hash_password(password: str) -> str:
    # bcrypt only uses the first 72 bytes of a password.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, name: str, email: str, password: str, role: str = "customer") -> UserModel:
        result = await self.db.execute(select(UserModel).where(UserModel.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        new_user = UserModel(name=name, email=email, password_hash=hash_password(password), role=role)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def authenticate_user(self, email: str, password: str) -> str:
        result = await self.db.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalar_one_or_none()

        if not user or not bcrypt.checkpw(password.encode("utf-8")[:72], user.password_hash.encode("utf-8")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": user.email, "role": user.role, "id": user.id, "exp": expire}
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
