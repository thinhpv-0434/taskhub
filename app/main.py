from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .core.lifespan import lifespan
from .api.v1.endpoints import router as api_router
from .api.v1.auth import router as auth_router

app = FastAPI(title="TaskHub API", lifespan=lifespan, version="1.0.0")
app.include_router(api_router)
app.include_router(auth_router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
