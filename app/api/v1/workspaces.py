from fastapi import APIRouter, Depends, status

from ...core.dependencies import get_current_user, get_workspace_service
from ...core.exceptions import ForbiddenException, NotFoundException
from ...db.models import User
from ...schemas.workspace import WorkspaceCreate, WorkspaceMemberCreate, WorkspaceRead
from ...services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


def _ensure_workspace_access(workspace, current_user: User) -> None:
    if current_user.id != workspace.owner_id and current_user.id not in {member.user_id for member in workspace.members}:
        raise ForbiddenException(detail="Access denied")


@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    service: WorkspaceService = Depends(get_workspace_service),
    current_user: User = Depends(get_current_user),
) -> WorkspaceRead:
    workspace = await service.create(payload, current_user.id)
    return WorkspaceRead.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: str,
    service: WorkspaceService = Depends(get_workspace_service),
    current_user: User = Depends(get_current_user),
) -> WorkspaceRead:
    workspace = await service.get(workspace_id)
    if not workspace:
        raise NotFoundException(detail="Workspace not found")
    _ensure_workspace_access(workspace, current_user)
    return WorkspaceRead.model_validate(workspace)


@router.post("/{workspace_id}/members", response_model=WorkspaceRead)
async def add_workspace_member(
    workspace_id: str,
    payload: WorkspaceMemberCreate,
    service: WorkspaceService = Depends(get_workspace_service),
    current_user: User = Depends(get_current_user),
) -> WorkspaceRead:
    workspace = await service.get(workspace_id)
    if not workspace:
        raise NotFoundException(detail="Workspace not found")
    if current_user.id != workspace.owner_id:
        raise ForbiddenException(detail="Only the workspace owner may add members")

    workspace = await service.add_member(workspace_id, payload.user_id, role=payload.role)
    return WorkspaceRead.model_validate(workspace)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    service: WorkspaceService = Depends(get_workspace_service),
    current_user: User = Depends(get_current_user),
) -> None:
    workspace = await service.get(workspace_id)
    if not workspace:
        raise NotFoundException(detail="Workspace not found")
    if current_user.id != workspace.owner_id:
        raise ForbiddenException(detail="Only the workspace owner may remove members")
    if user_id == workspace.owner_id:
        raise ForbiddenException(detail="Workspace owner cannot be removed")

    await service.remove_member(workspace_id, user_id)
