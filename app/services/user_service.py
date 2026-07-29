
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import hash_password
from ..db.models import User
from ..schemas.user import UserCreate, UserRead, UserUpdate


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: UserCreate) -> UserRead:
        existing = await self.db.execute(select(User).where(User.email == payload.email))
        if existing.scalars().first():
            raise ValueError("Email is already registered")

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return UserRead.model_validate(user)

    async def get(self, user_id: str) -> UserRead | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        return UserRead.model_validate(user) if user else None

    async def list(self) -> list[UserRead]:
        result = await self.db.execute(select(User))
        users = result.scalars().all()
        return [UserRead.model_validate(user) for user in users]

    async def update_profile(self, user_id: str, payload: UserUpdate) -> UserRead:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise ValueError("User not found")

        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.password is not None:
            user.hashed_password = hash_password(payload.password)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return UserRead.model_validate(user)
