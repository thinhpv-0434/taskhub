from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import create_access_token, create_refresh_token, hash_password, verify_password, decode_token
from ..db.models import User
from ..schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from ..schemas.user import UserRead


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, payload: RegisterRequest) -> UserRead:
        # Check if email already exists
        result = await self.db.execute(select(User).where(User.email == payload.email))
        existing_user = result.scalars().first()
        
        if existing_user:
            raise ValueError(f"Email {payload.email} is already registered")

        # Create new user
        hashed_password = hash_password(payload.password)
        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hashed_password,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return UserRead.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        # Find user by email
        result = await self.db.execute(select(User).where(User.email == payload.email))
        user = result.scalars().first()

        if not user or not verify_password(payload.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        # Create tokens (include role for RBAC)
        access_token = create_access_token(data={"sub": user.id, "email": user.email, "role": getattr(user, "role", "MEMBER")})
        refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email, "role": getattr(user, "role", "MEMBER")})

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)

        if not payload:
            raise ValueError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = payload.get("sub")
        
        # Verify user still exists and is active
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Create new tokens (preserve role)
        access_token = create_access_token(data={"sub": user.id, "email": user.email, "role": getattr(user, "role", "MEMBER")})
        new_refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email, "role": getattr(user, "role", "MEMBER")})

        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)

    async def logout(self) -> dict:
        return {"message": "Successfully logged out"}
