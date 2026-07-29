from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import User, Workspace, WorkspaceMember
from ..schemas.workspace import WorkspaceCreate


class WorkspaceService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: WorkspaceCreate, owner_id: str) -> Workspace:
        result = await self.db.execute(select(User).where(User.id == owner_id))
        owner = result.scalars().first()
        if not owner:
            raise ValueError("Owner not found")

        workspace = Workspace(
            name=payload.name,
            description=payload.description,
            owner_id=owner.id,
        )
        self.db.add(workspace)
        await self.db.flush()
        # create owner membership with OWNER role
        membership = WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role="OWNER")
        self.db.add(membership)

        await self.db.commit()
        return await self.get(workspace.id)

    async def get(self, workspace_id: str) -> Workspace | None:
        result = await self.db.execute(
            select(Workspace)
            .where(Workspace.id == workspace_id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Workspace.owner),
                selectinload(Workspace.members).selectinload(WorkspaceMember.user),
            )
        )
        return result.scalars().first()

    async def add_member(self, workspace_id: str, user_id: str, role: str | None = None) -> Workspace:
        workspace = await self.get(workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalars().first()
        if not user:
            raise ValueError("User not found")

        existing_result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        if existing_result.scalars().first():
            raise ValueError("User is already a workspace member")

        membership = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role or "EDITOR")
        self.db.add(membership)
        await self.db.commit()
        return await self.get(workspace_id)

    async def remove_member(self, workspace_id: str, user_id: str) -> None:
        membership_result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        membership = membership_result.scalars().first()
        if not membership:
            raise ValueError("Workspace member not found")

        await self.db.delete(membership)
        await self.db.commit()
