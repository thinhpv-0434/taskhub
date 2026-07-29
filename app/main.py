from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .core.lifespan import lifespan
from .api.v1.auth import router as auth_router
from .api.v1.users import router as user_router
from .api.v1.workspaces import router as workspace_router
from .api.v1.projects import router as project_router
from .api.v1.tasks import router as tasks_router
from .core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .core.middleware import LoggingMiddleware

app = FastAPI(title="TaskHub API", lifespan=lifespan, version="1.0.0")
app.add_middleware(LoggingMiddleware)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(workspace_router)
app.include_router(project_router)
app.include_router(tasks_router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
