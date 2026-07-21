from contextlib import asynccontextmanager
from typing import AsyncIterator

from ..db.session import engine, init_db


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    await init_db()
    yield
    await engine.dispose()