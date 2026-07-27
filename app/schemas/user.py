from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    is_active: bool = True
    role: UserRole = UserRole.MEMBER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None


class UserRead(UserBase):
    id: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}