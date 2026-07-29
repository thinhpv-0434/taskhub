from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Project
from ..schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from sqlalchemy.orm import selectinload


class ProjectService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: ProjectCreate) -> ProjectRead:
        proj = Project(**payload.model_dump(exclude_none=True))
        self.db.add(proj)
        await self.db.commit()
        return await self.get(proj.id)

    async def get(self, project_id: str) -> Optional[ProjectRead]:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id).options(selectinload(Project.owner), selectinload(Project.workspace))
        )
        obj = result.scalars().first()
        return ProjectRead.model_validate(obj) if obj else None

    async def list(self) -> List[ProjectRead]:
        result = await self.db.execute(select(Project).options(selectinload(Project.owner)))
        items = result.scalars().all()
        return [ProjectRead.model_validate(o) for o in items]

    async def update(self, project_id: str, payload: ProjectUpdate) -> Optional[ProjectRead]:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        obj = result.scalars().first()
        if not obj:
            return None
        for k, v in payload.model_dump(exclude_none=True).items():
            setattr(obj, k, v)
        self.db.add(obj)
        await self.db.commit()
        return await self.get(project_id)

    async def delete(self, project_id: str) -> bool:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        obj = result.scalars().first()
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True
