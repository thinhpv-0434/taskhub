from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import DATABASE_URL
from .base import Base

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_user_role_column)


def _ensure_user_role_column(sync_conn) -> None:
    """Ensure the users.role column exists for older SQLite databases."""
    if sync_conn.engine.name != "sqlite":
        return

    existing_columns = [row[1] for row in sync_conn.execute(text("PRAGMA table_info(users)")).fetchall()]
    if "role" not in existing_columns:
        sync_conn.execute(
            text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'MEMBER'")
        )