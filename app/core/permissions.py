import logging
from collections.abc import Iterable

from ..core.exceptions import ForbiddenException
from ..db.models import User, Workspace
from ..schemas.workspace import WorkspaceRole

logger = logging.getLogger("taskhub.permissions")


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
        logger.warning(
            "authorization_denied user_id=%s workspace_id=%s reason=not_a_member",
            user.id,
            workspace.id,
        )
        raise ForbiddenException(detail="Access denied")

    if allowed_roles is not None and role not in set(allowed_roles):
        logger.warning(
            "authorization_denied user_id=%s workspace_id=%s role=%s reason=insufficient_role",
            user.id,
            workspace.id,
            role.value,
        )
        raise ForbiddenException(detail="Insufficient workspace permissions")
    return role
