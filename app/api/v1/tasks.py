
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...core.dependencies import (
    get_current_user,
    get_project_service,
    get_task_list_cache,
    get_task_service,
    get_workspace_service,
)
from ...core.permissions import ensure_workspace_access, is_admin
from ...db.models import TaskStatus, User
from ...schemas.comment import CommentCreate, CommentRead
from ...schemas.task import TaskCreate, TaskRead, TaskUpdate
from ...schemas.workspace import WorkspaceRole
from ...services.cache_service import TaskListCache
from ...services.project_service import ProjectService
from ...services.task_service import TaskService
from ...services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/v1", tags=["tasks"])


async def _ensure_project_access(
    project,
    current_user: User,
    workspace_service: WorkspaceService,
    allowed_roles: tuple[WorkspaceRole, ...] | None = None,
) -> None:
    if is_admin(current_user) or (project.owner and project.owner.id == current_user.id):
        return
    if not project.workspace_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    workspace = await workspace_service.get(project.workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    ensure_workspace_access(workspace, current_user, allowed_roles)


async def _ensure_task_access(
    task: TaskRead,
    current_user: User,
    workspace_service: WorkspaceService,
    allowed_roles: tuple[WorkspaceRole, ...] | None = None,
) -> None:
    if is_admin(current_user):
        return
    if task.project:
        await _ensure_project_access(task.project, current_user, workspace_service, allowed_roles)
        return
    if task.assignee and task.assignee.id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task_under_project(
    project_id: str,
    payload: TaskCreate,
    project_service: ProjectService = Depends(get_project_service),
    service: TaskService = Depends(get_task_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    cache: TaskListCache = Depends(get_task_list_cache),
    current_user=Depends(get_current_user),
) -> TaskRead:
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await _ensure_project_access(
        project,
        current_user,
        workspace_service,
        (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
    )

    data = payload.model_dump()
    data["project_id"] = project_id
    task = await service.create(TaskCreate.model_validate(data))
    await cache.invalidate_project(project_id)
    return task


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
async def list_tasks_by_project(
    project_id: str,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: int | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: TaskService = Depends(get_task_service),
    project_service: ProjectService = Depends(get_project_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    cache: TaskListCache = Depends(get_task_list_cache),
    current_user: User = Depends(get_current_user),
) -> list[TaskRead]:
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await _ensure_project_access(project, current_user, workspace_service)
    cached = await cache.get(
        project_id,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        page=page,
        limit=limit,
    )
    if cached is not None:
        return cached

    tasks = await service.list_by_project(
        project_id,
        page=page,
        limit=limit,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
    )
    await cache.set(
        project_id,
        tasks,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        page=page,
        limit=limit,
    )
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    obj = await service.get(task_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await _ensure_task_access(obj, current_user, workspace_service)
    return obj


@router.post("/tasks/{task_id}/labels/{label_id}", response_model=TaskRead)
async def add_task_label(
    task_id: str,
    label_id: str,
    service: TaskService = Depends(get_task_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    cache: TaskListCache = Depends(get_task_list_cache),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    existing = await service.get(task_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await _ensure_task_access(
        existing,
        current_user,
        workspace_service,
        (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
    )
    try:
        task = await service.add_label(task_id, label_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.project:
        await cache.invalidate_project(task.project.id)
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
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    cache: TaskListCache = Depends(get_task_list_cache),
    current_user: User = Depends(get_current_user),
) -> CommentRead:
    existing = await service.get(task_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await _ensure_task_access(
        existing,
        current_user,
        workspace_service,
        (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
    )
    comment = await service.create_comment(task_id, current_user.id, payload)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if existing.project:
        await cache.invalidate_project(existing.project.id)
    return comment


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    cache: TaskListCache = Depends(get_task_list_cache),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    obj = await service.get(task_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await _ensure_task_access(
        obj,
        current_user,
        workspace_service,
        (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
    )
    updated = await service.update(task_id, payload)
    if obj.project:
        await cache.invalidate_project(obj.project.id)
    return updated


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    cache: TaskListCache = Depends(get_task_list_cache),
    current_user: User = Depends(get_current_user),
) -> None:
    obj = await service.get(task_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await _ensure_task_access(
        obj,
        current_user,
        workspace_service,
        (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
    )
    await service.delete(task_id)
    if obj.project:
        await cache.invalidate_project(obj.project.id)
    return None
