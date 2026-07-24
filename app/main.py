from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.exceptions import register_exception_handler
from app.core.logging_config import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_application() -> FastAPI:
    setup_logging(level="INFO")

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        # In production, disable docs exposure
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(RequestContextMiddleware)

    # Register exception handlers
    register_exception_handler(app)

    # Health check — no auth, no DB, always responds
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.app_name,
            "env": settings.app_env,
        }

    # Deep health check — tests DB
    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        from sqlalchemy import text
        from app.core.db_session import AsyncSessionLocal

        checks = {"database": False}

        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = True
        except Exception as e:
            checks["database_error"] = str(e)

        all_healthy = all(v is True for v in checks.values())
        return {
            "status": "ready" if all_healthy else "degraded",
            "checks": checks,
        }

    return app


app = create_application()
