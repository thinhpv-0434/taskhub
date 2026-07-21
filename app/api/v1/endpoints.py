from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import get_task_service
from ...schemas.task import TaskCreate, TaskRead

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead)
async def create_task(payload: TaskCreate, service=Depends(get_task_service)):
    return await service.create(payload)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: str, service=Depends(get_task_service)):
    task = await service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task