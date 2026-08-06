import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.slots.model import Slot, SlotStatus


async def add(db: AsyncSession, slot: Slot) -> None:
    db.add(slot)

async def list_all_by_tenant(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[Slot]:
    result = await db.execute(
        select(Slot).where(
            Slot.tenant_id == tenant_id
        )
    )
    return list(result.scalars().all())

async def list_available_by_tenant(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[Slot]:
    result = await db.execute(
        select(Slot).where(
            Slot.tenant_id == tenant_id, Slot.status == SlotStatus.AVAILABLE
        )
    )
    return list(result.scalars().all())


async def get_for_update_by_id_and_tenant(
    db: AsyncSession, slot_id: uuid.UUID, tenant_id: uuid.UUID
) -> Slot | None:
    """Row-locked read — used by bookings/service.py's create_booking to
    take the concurrency-safety lock. Exposed here (not duplicated in
    bookings' own repository) because the Slot table is owned by this
    feature; bookings depends on slots for this read, matching the same
    one-way dependency direction already enforced at the model layer."""
    result = await db.execute(
        select(Slot)
        .where(Slot.id == slot_id, Slot.tenant_id == tenant_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def get_by_id_and_tenant(
    db: AsyncSession, slot_id: uuid.UUID, tenant_id: uuid.UUID
) -> Slot | None:
    result = await db.execute(
        select(Slot).where(Slot.id == slot_id, Slot.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, slot_id: uuid.UUID) -> Slot:
    """Unscoped by tenant — used only by bookings/service.py's
    cancel_booking, which has ALREADY verified tenant ownership via the
    Booking row it fetched first. Not exposed for any tenant-unverified
    lookup path."""
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    return result.scalar_one()
