from datetime import datetime
from pydantic import BaseModel, EmailStr
from sqlalchemy import BigInteger, Column, DateTime, String, func
from app.core.database import Base, ID_TYPE

class UserModel(Base):
    __tablename__ = "users"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="customer")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# Pydantic Schemas
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True