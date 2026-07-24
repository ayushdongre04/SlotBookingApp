from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.config import settings

engine = create_async_engine(
    url=settings.database_url,
    echo=settings.debug,  # logs all SQL in development
    pool_size=10,  # keep 10 connections open
    max_overflow=20,  # allow 20 extra under load
    pool_pre_ping=True,  # test connections before using (prevents stale)
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,  # don't expire objects after commit
    # so we can access them after the transaction ends
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # session = AsyncSessionLocal()
    # try:
    #     yield session
    # finally:
    #     await session.close()

    async with AsyncSessionLocal() as session:
        yield session
