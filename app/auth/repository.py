import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.model import User


async def add(db: AsyncSession, user: User) -> None:
    db.add(user)


async def get_by_tenant_and_email(
    db: AsyncSession, tenant_id: uuid.UUID, email: str
) -> User | None:
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.email == email)
    )
    return result.scalar_one_or_none()