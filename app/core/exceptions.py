import logging
import uuid

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """
    Base for every domain-level error. Routers/services raise these;
    they know nothing about HTTP. The mapping to a status code lives only
    in register_exception_handlers — one place to change it.
    """

    status_code = 500
    error_code = "internal_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"


class ValidationError(AppError):
    status_code = 400
    error_code = "validation_error"


def register_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exec: AppError):
        logger.warning(
            "handled application error",
            extra={
                "ctx_error_code": exec.error_code,
                "ctx_path": request.url.path
            }
        )

        return JSONResponse(
            status_code=exec.status_code,
            content={"error_code": exec.error_code, "message": exec.message}
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exec: Exception):
        # Anything that reaches here is a bug, not an expected business
        # condition — log the full stack trace, but never leak it to the
        # client. That's the line between a debuggable system and a
        # security problem.
        incident_id = str(uuid.uuid4())
        logger.error(
            "unhandled exception",
            exc_info=exec,
            extra={"ctx_incident_id": incident_id, "ctx_path": request.url.path},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "internal_error",
                "message": "Something went wrong. Reference this ID when reporting.",
                "incident_id": incident_id,
            },
        )