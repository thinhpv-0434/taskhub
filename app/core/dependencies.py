from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import decode_token
from ..db.models import User
from ..db.session import get_db
from ..services.auth_service import AuthService
from ..services.task_service import TaskService
from ..services.user_service import UserService


async def get_task_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[TaskService, None]:
    yield TaskService(db)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[AuthService, None]:
    yield AuthService(db)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[UserService, None]:
    yield UserService(db)


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep