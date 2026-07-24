import logging
from math import log
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.context import request_id_var

logger = logging.getLogger(__name__)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Assigns a request ID (or reuses one passed in by an upstream service
    via X-Request-ID — common in microservice chains), logs one line per
    request with timing, and echoes the ID back so the client can quote it
    when reporting an issue.
    """

    async def dispatch(self, request, call_next):
        incomming_id = request.headers.get("x-request-id")
        request_id = incomming_id or str(uuid.uuid4())
        token = request_id_var.set(request_id)

        start = time.monotonic()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        logger.info(
            "request completed",
            extra={
                "ctx_method": request.method,
                "ctx_path": request.url.path,
                "ctx_status_code": response.status_code,
                "ctx_duration_ms": duration_ms
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response