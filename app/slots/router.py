import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.slots import service
from app.slots.schemas import SlotCreateSchema, SlotResponseSchema
from app.core.tenancy import get_current_tenant_id
from app.slots.sse import slot_events_stream

router = APIRouter(prefix="/slots", tags=["slots"])


@router.post("", response_model=SlotResponseSchema, status_code=201)
async def create_slot(
    slot_create: SlotCreateSchema,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id)
):
    """
    Create a new slot.
    Args:
        slot_create (SlotResponseSchema): The schema containing the slot data to create.
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        tenant_id (uuid.UUID): The ID of the tenant to which the slot belongs.
    Returns:
        SlotResponseSchema: The newly created slot instance.
    """
    slot = await service.create_slot_service(db, slot_create, tenant_id)
    return slot

# Before /slots/{slot_id} endpoint, to avoid conflict with /slots/available endpoint
@router.get("/available", response_model=list[SlotResponseSchema])
async def get_available_slots(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id)
):
    """
    Retrieve all available slots.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        tenant_id (uuid.UUID): The ID of the tenant to which the slots belong.
    Returns:
        list[SlotResponseSchema]: A list of all available slot instances.
    """
    slots = await service.get_available_slots_service(db, tenant_id)
    return slots


@router.get("", response_model=list[SlotResponseSchema])
async def get_all_slots(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id)
):
    """
    Retrieve all slots.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        tenant_id (uuid.UUID): The ID of the tenant to which the slots belong.
    Returns:
        list[SlotResponseSchema]: A list of all slot instances.
    """
    slots = await service.get_all_slots_service(db, tenant_id)
    return slots

@router.get("/stream")
async def stream_slot_events(
    request: Request,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
):
    """
    Server-Sent Events endpoint — a browser opens this once and
    receives a live push every time a slot in this tenant is booked or
    freed, instead of polling GET /slots on an interval.
    """
    return StreamingResponse(
        slot_events_stream(request, tenant_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{slot_id}", response_model=SlotResponseSchema)
async def get_slot_by_id(
    slot_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id)
):
    """
    Retrieve a slot by its ID.
    Args:
        slot_id (uuid.UUID): The ID of the slot to retrieve.
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        tenant_id (uuid.UUID): The ID of the tenant to which the slot belongs.
    Returns:
        SlotResponseSchema | None: The slot instance if found, otherwise None.
    """
    slot = await service.get_slot_by_id_service(db, slot_id, tenant_id)
    return slot
