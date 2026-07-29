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
    role: str | None = None


class WorkspaceRead(WorkspaceBase):
    id: str
    owner: UserRead | None = None
    members: list[UserRead] = Field(default_factory=list, alias="member_users")
    # expose member roles (workspace member model includes role)
    member_roles: dict[str, str] = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}
