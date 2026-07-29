from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import Project, Task
from ..schemas.task import TaskCreate, TaskRead


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: TaskCreate) -> TaskRead:
        task = Task(**payload.model_dump(exclude_none=True))
        self.db.add(task)
        await self.db.commit()
        return await self.get(task.id)

    async def get(self, task_id: str) -> Optional[TaskRead]:
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.project).selectinload(Project.owner),
                selectinload(Task.assignee),
            )
        )
        task = result.scalars().first()
        return TaskRead.model_validate(task) if task else None

    async def list_by_project(
        self,
        project_id: str,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        priority: int | None = None,
        assignee_id: str | None = None,
    ) -> list[TaskRead]:
        stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .options(
                selectinload(Task.project).selectinload(Project.owner),
                selectinload(Task.assignee),
            )
        )
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if assignee_id is not None:
            stmt = stmt.where(Task.assignee_id == assignee_id)

        offset = (max(page, 1) - 1) * max(limit, 1)
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return [TaskRead.model_validate(i) for i in items]

    async def update(self, task_id: str, payload) -> Optional[TaskRead]:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            return None
        for k, v in payload.model_dump(exclude_none=True).items():
            setattr(task, k, v)
        self.db.add(task)
        await self.db.commit()
        return await self.get(task_id)

    async def delete(self, task_id: str) -> bool:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            return False
        await self.db.delete(task)
        await self.db.commit()
        return True
