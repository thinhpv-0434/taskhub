from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.dependencies import get_project_service, get_current_user, get_workspace_service
from ...core.permissions import ensure_workspace_access, is_admin
from ...db.models import User
from ...schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from ...schemas.workspace import WorkspaceRole
from ...services.project_service import ProjectService
from ...services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


async def _ensure_project_access(
    project: ProjectRead,
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


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> ProjectRead:
    if payload.workspace_id:
        workspace = await workspace_service.get(payload.workspace_id)
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        ensure_workspace_access(
            workspace,
            current_user,
            (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
        )
        owner_is_member = payload.owner_id == workspace.owner_id or any(
            member.user_id == payload.owner_id for member in workspace.members
        )
        if payload.owner_id != current_user.id and not is_admin(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create a project for another user")
        if not owner_is_member and payload.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project owner is not a workspace member")
    elif payload.owner_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create a project for another user")

    return await service.create(payload)


@router.get("/", response_model=List[ProjectRead])
async def list_projects(
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user),
) -> List[ProjectRead]:
    return await service.list_for_user(current_user.id, is_admin=is_admin(current_user))


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    obj = await service.get(project_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await _ensure_project_access(obj, current_user, workspace_service)
    return obj


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    obj = await service.get(project_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await _ensure_project_access(
        obj,
        current_user,
        workspace_service,
        (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
    )
    if payload.workspace_id and payload.workspace_id != obj.workspace_id:
        target_workspace = await workspace_service.get(payload.workspace_id)
        if not target_workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        ensure_workspace_access(
            target_workspace,
            current_user,
            (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
        )
    updated = await service.update(project_id, payload)
    return updated


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    current_user: User = Depends(get_current_user),
) -> None:
    obj = await service.get(project_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await _ensure_project_access(
        obj,
        current_user,
        workspace_service,
        (WorkspaceRole.OWNER, WorkspaceRole.EDITOR),
    )
    await service.delete(project_id)
    return None
