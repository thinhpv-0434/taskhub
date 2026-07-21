from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..services.task_service import TaskService


async def get_task_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[TaskService, None]:
    yield TaskService(db)