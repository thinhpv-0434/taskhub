from collections.abc import Iterable

from ..core.exceptions import ForbiddenException
from ..db.models import User, Workspace
from ..schemas.workspace import WorkspaceRole


def is_admin(user: User) -> bool:
    role = getattr(user, "role", None)
    return getattr(role, "value", role) == "ADMIN"


def get_workspace_role(workspace: Workspace, user: User) -> WorkspaceRole | None:
    if user.id == workspace.owner_id:
        return WorkspaceRole.OWNER

    for member in workspace.members:
        if member.user_id == user.id:
            try:
                return WorkspaceRole(member.role)
            except ValueError:
                return None
    return None


def ensure_workspace_access(
    workspace: Workspace,
    user: User,
    allowed_roles: Iterable[WorkspaceRole] | None = None,
) -> WorkspaceRole | None:
    if is_admin(user):
        return None

    role = get_workspace_role(workspace, user)
    if role is None:
        raise ForbiddenException(detail="Access denied")

    if allowed_roles is not None and role not in set(allowed_roles):
        raise ForbiddenException(detail="Insufficient workspace permissions")
    return role
