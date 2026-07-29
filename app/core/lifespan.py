from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ..db.session import engine, init_db


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    await init_db()
    yield
    await engine.dispose()