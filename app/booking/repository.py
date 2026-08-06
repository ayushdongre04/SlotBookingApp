import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.booking.model import Booking


async def add(db: AsyncSession, booking: Booking) -> None:
    db.add(booking)


async def get_by_id_and_tenant(
    db: AsyncSession, booking_id: uuid.UUID, tenant_id: uuid.UUID
) -> Booking | None:
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def list_all_by_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> list[Booking]:
    result = await db.execute(select(Booking).where(Booking.tenant_id == tenant_id))
    return list(result.scalars().all())
