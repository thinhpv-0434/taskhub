from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Task
from ..schemas.task import TaskCreate, TaskRead


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: TaskCreate) -> TaskRead:
        task = Task(**payload.model_dump(exclude_none=True))
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return TaskRead.model_validate(task)

    async def get(self, task_id: str) -> Optional[TaskRead]:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        return TaskRead.model_validate(task) if task else None