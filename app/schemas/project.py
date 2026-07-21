from datetime import datetime
from pydantic import BaseModel

from .user import UserRead


class ProjectBase(BaseModel):
    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    owner_id: str


class ProjectRead(ProjectBase):
    id: str
    owner: UserRead | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}