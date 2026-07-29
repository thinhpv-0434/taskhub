from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...core.dependencies import get_task_service, get_project_service, get_current_user, get_workspace_service
from ...db.models import TaskStatus
from ...schemas.comment import CommentCreate, CommentRead
from ...schemas.task import TaskCreate, TaskRead, TaskUpdate
from ...services.task_service import TaskService
from ...services.project_service import ProjectService
from ...services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task_under_project(
    project_id: str,
    payload: TaskCreate,
    project_service: ProjectService = Depends(get_project_service),
    service: TaskService = Depends(get_task_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    current_user=Depends(get_current_user),
) -> TaskRead:
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # if project is in a workspace, ensure current_user is a member with access
    workspace_id = getattr(project, "workspace_id", None)
    if workspace_id:
        ws = await workspace_service.get(workspace_id)
        if not any(m.user_id == current_user.id for m in ws.members) and current_user.role != "ADMIN":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")

    data = payload.model_dump()
    data["project_id"] = project_id
    task = await service.create(TaskCreate.model_validate(data))
    return task


@router.get("/projects/{project_id}/tasks", response_model=List[TaskRead])
async def list_tasks_by_project(
    project_id: str,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: int | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: TaskService = Depends(get_task_service),
) -> List[TaskRead]:
    return await service.list_by_project(
        project_id,
        page=page,
        limit=limit,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: str, service: TaskService = Depends(get_task_service)) -> TaskRead:
    obj = await service.get(task_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return obj


@router.post("/tasks/{task_id}/labels/{label_id}", response_model=TaskRead)
async def add_task_label(
    task_id: str,
    label_id: str,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
) -> TaskRead:
    try:
        task = await service.add_label(task_id, label_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_comment(
    task_id: str,
    payload: CommentCreate,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
) -> CommentRead:
    comment = await service.create_comment(task_id, current_user.id, payload)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return comment


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: str, payload: TaskUpdate, service: TaskService = Depends(get_task_service), current_user=Depends(get_current_user)) -> TaskRead:
    obj = await service.get(task_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    updated = await service.update(task_id, payload)
    return updated


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, service: TaskService = Depends(get_task_service), current_user=Depends(get_current_user)) -> None:
    obj = await service.get(task_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await service.delete(task_id)
    return None
