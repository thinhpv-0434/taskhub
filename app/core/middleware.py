from __future__ import annotations

import time
from logging import getLogger

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = getLogger("taskhub.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        elapsed = (time.time() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{elapsed:.2f}ms"
        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response