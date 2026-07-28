from datetime import datetime

from pydantic import BaseModel, Field

from .user import UserRead


class WorkspaceBase(BaseModel):
    name: str
    description: str | None = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceMemberCreate(BaseModel):
    user_id: str


class WorkspaceRead(WorkspaceBase):
    id: str
    owner: UserRead | None = None
    members: list[UserRead] = Field(default_factory=list, alias="member_users")
    created_at: datetime | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}
