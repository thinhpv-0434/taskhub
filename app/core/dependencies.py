import logging
from collections.abc import AsyncGenerator

from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import CACHE_TTL_SECONDS
from ..core.exceptions import ForbiddenException, UnauthorizedException
from ..core.security import decode_token
from ..db.models import User
from ..db.session import get_db
from ..services.auth_service import AuthService
from ..services.cache_service import TaskListCache
from ..services.project_service import ProjectService
from ..services.task_service import TaskService
from ..services.user_service import UserService
from ..services.workspace_service import WorkspaceService

logger = logging.getLogger("taskhub.auth")


def get_task_list_cache(request: Request) -> TaskListCache:
    redis = getattr(request.app.state, "redis", None)
    return TaskListCache(redis, CACHE_TTL_SECONDS)


async def get_task_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[TaskService, None]:
    yield TaskService(db)


async def get_project_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[ProjectService, None]:
    yield ProjectService(db)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[AuthService, None]:
    yield AuthService(db)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[UserService, None]:
    yield UserService(db)


async def get_workspace_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[WorkspaceService, None]:
    yield WorkspaceService(db)


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        logger.warning("authentication_denied reason=missing_or_invalid_scheme")
        raise UnauthorizedException(detail="Missing or invalid authorization token")

    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        logger.warning("authentication_denied reason=invalid_or_expired_token")
        raise UnauthorizedException(detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalars().first()
    if not user:
        logger.warning("authentication_denied reason=user_not_found user_id=%s", payload["sub"])
        raise UnauthorizedException(detail="User not found")

    logger.debug("authentication_succeeded user_id=%s", user.id)
    return user


def require_roles(*roles):
    """Return a dependency that ensures the current user has one of the given roles.

    Usage: Depends(require_roles(UserRole.ADMIN))
    """
    from ..schemas.user import UserRole as _UserRole

    def _dep(user: User = Depends(get_current_user)) -> User:
        user_role = getattr(user, "role", None)
        # Normalize role values to strings for comparison
        if isinstance(user_role, _UserRole):
            current = user_role.value
        else:
            current = str(user_role)

        allowed = {r.value if isinstance(r, _UserRole) else str(r) for r in roles}
        if current not in allowed:
            raise ForbiddenException(detail="Forbidden")
        return user

    return _dep
