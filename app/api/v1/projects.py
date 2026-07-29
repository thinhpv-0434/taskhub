from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.dependencies import get_project_service, require_roles, get_current_user, get_workspace_service
from ...schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from ...schemas.user import UserRole
from ...services.project_service import ProjectService
from ...services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    _admin=Depends(require_roles(UserRole.ADMIN)),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> ProjectRead:
    # check workspace membership if workspace_id provided
    if payload.workspace_id:
        ws = await workspace_service.get(payload.workspace_id)
        if not ws:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        # must be owner or have role OWNER/EDITOR
        if not any(m.user_id == payload.owner_id and m.role in ("OWNER", "EDITOR") for m in ws.members):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create project in this workspace")

    return await service.create(payload)


@router.get("/", response_model=List[ProjectRead])
async def list_projects(service: ProjectService = Depends(get_project_service)) -> List[ProjectRead]:
    return await service.list()


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str, service: ProjectService = Depends(get_project_service)) -> ProjectRead:
    obj = await service.get(project_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return obj


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
    current_user=Depends(get_current_user),
) -> ProjectRead:
    obj = await service.get(project_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # only owner or admin can update
    if obj.owner and obj.owner.id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    updated = await service.update(project_id, payload)
    return updated


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    current_user=Depends(get_current_user),
) -> None:
    obj = await service.get(project_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if obj.owner and obj.owner.id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await service.delete(project_id)
    return None
