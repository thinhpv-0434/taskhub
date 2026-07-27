from typing import List

from fastapi import APIRouter, Depends, status

from ...core.dependencies import get_user_service, get_current_user, require_roles
from ...schemas.user import UserCreate, UserRead, UserUpdate, UserRole
from ...services.user_service import UserService
from ...db.models import User
from ...core.exceptions import NotFoundException

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> UserRead:
    try:
        return await service.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=List[UserRead])
async def list_users(service: UserService = Depends(get_user_service), admin: User = Depends(require_roles(UserRole.ADMIN))) -> List[UserRead]:
    return await service.list()


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.update_profile(current_user.id, payload)


@router.get("/id/{user_id}", response_model=UserRead)
async def get_user(user_id: str, service: UserService = Depends(get_user_service)) -> UserRead:
    user = await service.get(user_id)
    if not user:
        raise NotFoundException(detail="User not found")
    return user
