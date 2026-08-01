import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.exceptions import register_exception_handler
from app.core.logging_config import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.config import settings

from app.booking.router import router as booking_router
from app.slots.router import router as slots_router
from app.providers.router import router as provider_router
from app.auth.router import router as auth_router


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
    )

    app.add_middleware(RequestContextMiddleware)

    # Register exception handlers
    register_exception_handler(app)

    # Register routers
    app.include_router(booking_router)
    app.include_router(slots_router)
    app.include_router(provider_router)
    app.include_router(auth_router)

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
        from redis.asyncio import from_url as redis_from_url

        checks = {"database": False, "redis": False}

        try:
            async with asyncio.timeout(5):
                async with AsyncSessionLocal() as session:
                    await session.execute(text("SELECT 1"))
            checks["database"] = True
        except TimeoutError:
            checks["database_error"] = "Database health check timed out"
        except Exception as e:
            checks["database_error"] = str(e)

        try:
            async with asyncio.timeout(5):
                redis_client = redis_from_url(settings.redis_url)
                await redis_client.ping()
                await redis_client.aclose()
            checks["redis"] = True
        except TimeoutError:
            checks["redis_error"] = "Redis health check timed out"
        except Exception as e:
            checks["redis_error"] = str(e)

        all_healthy = all(v is True for v in checks.values())
        return {
            "status": "ready" if all_healthy else "degraded",
            "checks": checks,
        }

    return app


app = create_application()
