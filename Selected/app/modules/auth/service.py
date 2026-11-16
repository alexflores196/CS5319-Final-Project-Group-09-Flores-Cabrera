import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.models import UserModel

SECRET_KEY = "your-super-secret-key-change-in-production"  # In production, use an environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, name: str, email: str, password: str, role: str = "customer") -> UserModel:
        # Check if email already exists
        result = await self.db.execute(select(UserModel).where(UserModel.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Hash password safely (72-byte limit safety)
        pwd_bytes = password.encode('utf-8')[:72]
        password_hash = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')

        new_user = UserModel(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def authenticate_user(self, email: str, password: str) -> str:
        result = await self.db.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

        pwd_bytes = password.encode('utf-8')[:72]
        if not bcrypt.checkpw(pwd_bytes, user.password_hash.encode('utf-8')):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

        # Generate JWT Token
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": user.email, "role": user.role, "id": user.id, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt