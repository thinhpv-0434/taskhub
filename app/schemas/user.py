from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}