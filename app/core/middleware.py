from __future__ import annotations

import time
from logging import getLogger
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = getLogger("taskhub.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        start_time = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{elapsed:.2f}ms"
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response
