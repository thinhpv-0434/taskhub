"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.dependencies import get_auth_service
from ...schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, LogoutRequest
from ...schemas.user import UserRead
from ...services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)) -> UserRead:
    try:
        return await auth_service.register(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    try:
        return await auth_service.login(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    try:
        return await auth_service.refresh(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(payload: LogoutRequest, auth_service: AuthService = Depends(get_auth_service)) -> dict:
    return await auth_service.logout()
