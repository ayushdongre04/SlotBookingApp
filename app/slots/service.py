import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.providers.model import Provider
from app.slots import repository
from app.slots.model import Slot, SlotStatus
from app.slots.schemas import SlotCreateSchema
from app.providers import repository as providers_repository

logger = logging.getLogger(__name__)

async def create_slot_service(
    db: AsyncSession,
    slot_create: SlotCreateSchema,
    tenant_id: uuid.UUID,
) -> Slot:
    """
    Create a new slot in the database.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        slot_create (SlotCreateSchema): The schema containing the slot data to create.
        tenant_id (uuid.UUID): The ID of the tenant to which the slot belongs.
    Returns:
        Slot: The newly created slot instance.
    """
    if slot_create.end_time <= slot_create.start_time:
        raise ValidationError("end_time must be after start_time")

    provider = await providers_repository.get_by_id_and_tenant(
        db=db,
        provider_id=slot_create.provider_id,
        tenant_id=tenant_id
    )

    if not provider:
        raise NotFoundError(
            f"Provider with ID {slot_create.provider_id} not found."
        )

    slot = Slot(
        provider_id=slot_create.provider_id,
        start_time=slot_create.start_time,
        end_time=slot_create.end_time,
        status=SlotStatus.AVAILABLE,
        tenant_id=tenant_id,
    )
    await repository.add(db, slot)
    await db.flush()  # Flush to get the ID assigned by the database
    await db.refresh(slot)  # Refresh to get the latest state from the database
    await db.commit()
    return slot


async def get_slot_by_id_service(
    db: AsyncSession,
    slot_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> Slot | None:
    """
    Retrieve a slot from the database by its ID.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        slot_id (uuid.UUID): The ID of the slot to retrieve.
        tenant_id (uuid.UUID): The ID of the tenant to which the slot belongs.
    Returns:
        Slot | None: The slot instance if found, otherwise None.
    """
    result = await repository.get_by_id_and_tenant(db=db, slot_id=slot_id, tenant_id=tenant_id)

    if not result:
        raise NotFoundError(f"Slot with ID {slot_id} not found.")

    return result


async def get_all_slots_service(
    db: AsyncSession,
    tenant_id: uuid.UUID
) -> list[Slot]:
    """
    Retrieve all slots from the database.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        tenant_id (uuid.UUID): The ID of the tenant to which the slots belong.
    Returns:
        list[Slot]: A list of all slot instances.
    """
    return await repository.list_all_by_tenant(db=db, tenant_id=tenant_id)


async def get_available_slots_service(
    db: AsyncSession,
    tenant_id: uuid.UUID
) -> list[Slot]:
    """
    Retrieve all available slots from the database.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        tenant_id (uuid.UUID): The ID of the tenant to which the slots belong.
    Returns:
        list[Slot]: A list of all available slot instances.
    """
    return await repository.list_available_by_tenant(db, tenant_id)
