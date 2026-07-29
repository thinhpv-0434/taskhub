from datetime import datetime
from pydantic import BaseModel

from .user import UserRead


class ProjectBase(BaseModel):
    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    owner_id: str
    workspace_id: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    workspace_id: str | None = None


class ProjectRead(ProjectBase):
    id: str
    owner: UserRead | None = None
    workspace_id: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}