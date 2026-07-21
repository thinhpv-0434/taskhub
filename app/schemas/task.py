from datetime import datetime
from pydantic import BaseModel

from .project import ProjectRead
from .user import UserRead


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: str = "todo"
    priority: int = 0
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    project_id: str | None = None
    assignee_id: str | None = None


class TaskRead(TaskBase):
    id: str
    project: ProjectRead | None = None
    assignee: UserRead | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}