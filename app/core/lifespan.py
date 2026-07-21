from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: init resources
    app.state.db = {"connected": True, "items": {}}
    print("[lifespan] startup: in-memory db initialized")
    try:
        yield
    finally:
        # Shutdown: cleanup
        app.state.db.clear()
        print("[lifespan] shutdown: in-memory db cleaned")
