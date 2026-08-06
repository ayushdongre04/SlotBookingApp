from sqlalchemy.ext.asyncio import AsyncSession

from app.tenants.model import Tenant


async def add(db: AsyncSession, tenant: Tenant) -> None:
    db.add(tenant)