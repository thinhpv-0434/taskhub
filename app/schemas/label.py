from datetime import datetime

from pydantic import BaseModel


class LabelRead(BaseModel):
    id: str
    name: str
    color: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
