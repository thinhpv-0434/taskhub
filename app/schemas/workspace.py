from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .user import UserRead


class WorkspaceRole(str, Enum):
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class WorkspaceBase(BaseModel):
    name: str
    description: str | None = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceMemberCreate(BaseModel):
    user_id: str
    role: WorkspaceRole = WorkspaceRole.EDITOR


class WorkspaceRead(WorkspaceBase):
    id: str
    owner: UserRead | None = None
    members: list[UserRead] = Field(default_factory=list, alias="member_users")
    # expose member roles (workspace member model includes role)
    member_roles: dict[str, str] = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}
