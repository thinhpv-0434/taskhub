from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from ..core.config import REDIS_URL
from ..db.session import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis_client: Redis | None = None
    await init_db()
    if REDIS_URL:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        app.state.redis = redis_client

    try:
        yield
    finally:
        if redis_client:
            await redis_client.aclose()
        await engine.dispose()
