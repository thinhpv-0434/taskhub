from datetime import datetime

from pydantic import BaseModel, Field

from .user import UserRead


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)


class CommentRead(BaseModel):
    id: str
    content: str
    author: UserRead
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
