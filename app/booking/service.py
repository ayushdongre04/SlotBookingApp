import asyncio
import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from typing import List

from app.booking.schemas import BookingCreate
from app.core.redis_client import redis_client, slot_events_channel
from app.core.exceptions import NotFoundError, ConflictError
from app.slots.model import Slot, SlotStatus
from app.booking.model import Booking, BookingStatus
from app.booking.tasks import (
    send_booking_confirmation,
    send_booking_cancellation,
)

logger = logging.getLogger(__name__)


async def _publish_slot_event(tenant_id: uuid.UUID, slot_id: uuid.UUID, status: SlotStatus) -> None:
    """Broadcasts a slot-availability change to any SSE connection
    subscribed to this tenant's channel, on ANY worker process — Redis
    Pub/Sub is what makes this visible across workers, not just within
    the process that handled this request.

    Deliberately isolated in its own try/except: a Redis Pub/Sub outage
    should degrade real-time UI updates, not fail the booking/cancel
    request that triggered it. SSE is a nice-to-have on top of a
    correct booking, not a dependency of one.
    """
    try:
        payload = {
            "slot_id": str(slot_id),
            "status": status.value,
        }

        await redis_client.publish(
            slot_events_channel(tenant_id=tenant_id),
            json.dumps(payload)
        )
    except Exception:
        logger.warning(
            "failed to publish slot event",
            exc_info=True,
            extra={"ctx_slot_id": str(slot_id), "ctx_status": status.value}
        )


async def create_booking(db: AsyncSession, payload: BookingCreate, tenant_id: uuid.UUID) -> Booking:
    """
    Create a new booking in the database.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        payload (BookingCreate): The schema containing the booking data to create.
        tenant_id (uuid.UUID): The ID of the tenant to which the booking belongs.
    Returns:
        Booking: The newly created booking instance.
    Raises:
        NotFoundError: If the slot with the given ID does not exist.
        ConflictError: If the slot is already booked or not available.
    """
    # Check if the slot exists
    slot_result = await db.execute(
        select(Slot).where(
            Slot.id == payload.slot_id,
            Slot.tenant_id == tenant_id
            ).with_for_update()
    )
    slot = slot_result.scalar_one_or_none()

    if not slot:
        raise NotFoundError(f"Slot with ID {payload.slot_id} not found.")

    # Check if the slot is available
    if slot.status != SlotStatus.AVAILABLE:
        raise ConflictError(
            f"Slot with ID {payload.slot_id} is not available for booking."
        )

    # Create the booking
    booking = Booking(
        tenant_id=tenant_id,
        slot_id=payload.slot_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        status=BookingStatus.CONFIRMED,
    )
    db.add(booking)
    await db.flush()  # Flush to get the ID assigned by the database

    # Update the slot status to booked
    slot.status = SlotStatus.BOOKED
    await db.commit()
    await db.refresh(booking)

    # Booking already committed successfully at this point — neither of
    # the two calls below should be able to turn a successful booking
    # into a failed API response if Redis/Celery has an issue.

    logger.info(
        "Booking created successfully",
        extra={"ctx_booking_id": booking.id, "ctx_slot_id": slot.id},
    )

    try:
        # Celery's .delay() is a SYNCHRONOUS, blocking call (it publishes to
        # Redis over a plain socket) — calling it directly here would block
        # the async event loop for that duration. Running it in a worker
        # thread via anyio / asyncio keeps this coroutine non-blocking.
        # await anyio.to_thread.run_sync(
        #     send_booking_confirmation.delay, str(booking.id), booking.customer_email
        # )
        await asyncio.to_thread(
            send_booking_confirmation.delay,
            str(booking.id),
            booking.customer_email
        )
    except Exception:
        # Booking already committed successfully — a notification enqueue
        # failure should never fail the API response. Logging it as a warning.
        logger.warning(
            "failed to enqueue booking confirmation",
            exc_info=True,
            extra={"ctx_booking_id": str(booking.id)},
        )

    await _publish_slot_event(
        tenant_id = tenant_id,
        slot_id = slot.id,
        status = SlotStatus.BOOKED)

    return booking


async def cancel_booking(db: AsyncSession, booking_id: uuid.UUID, tenant_id: uuid.UUID) -> Booking:
    """
    Cancel an existing booking in the database.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        booking_id (uuid.UUID): The ID of the booking to cancel.
        tenant_id (uuid.UUID): The ID of the tenant to which the booking belongs.
    Returns:
        Booking: The updated booking instance with status set to CANCELLED.
    Raises:
        NotFoundError: If the booking with the given ID does not exist.
        ConflictError: If the booking is already cancelled or completed.
    """
    # selectinload is used to eagerly load the related slot when fetching the booking.
    # This avoids lazy loading issues and ensures that the slot is available for status update when cancelling the booking.
    stmt = (
        select(Booking)
        .options(selectinload(Booking.slot))
        .where(Booking.id == booking_id, Booking.tenant_id == tenant_id)
        .with_for_update()
    )

    # Retrieve the booking
    booking_result = await db.execute(stmt)

    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise NotFoundError(f"Booking with ID {booking_id} not found.")

    if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        raise ConflictError(
            f"Booking with ID {booking_id} cannot be cancelled as it is already {booking.status.value}."
        )

    booking.status = BookingStatus.CANCELLED
    booking.slot.status = SlotStatus.AVAILABLE  # Update the slot status to available
    await db.commit()
    await db.refresh(booking)

    logger.info(
        f"Booking cancelled successfully",
        extra={"ctx_booking_id": booking.id, "ctx_slot_id": booking.slot.id},
    )

    try:
        await asyncio.to_thread(
            send_booking_cancellation.delay,
            str(booking.id),
            booking.customer_email
        )
    except Exception:
        # Booking already cancelled successfully — a notification enqueue
        # failure should never fail the API response. Logging it as a warning.
        logger.warning(
            "failed to enqueue booking cancellation",
            exc_info=True,
            extra={"ctx_booking_id": str(booking.id)},
        )

    await _publish_slot_event(
        tenant_id = tenant_id,
        slot_id = booking.slot.id,
        status = SlotStatus.AVAILABLE
    )

    return booking


async def get_all_bookings(db: AsyncSession, tenant_id: uuid.UUID) -> List[Booking]:
    """Retrieve all bookings with their related slots."""
    stmt = select(Booking).options(selectinload(Booking.slot)).where(Booking.tenant_id == tenant_id)
    result = await db.execute(stmt)
    bookings = result.scalars().all()
    return bookings


async def get_booking_by_id(db: AsyncSession, booking_id: uuid.UUID, tenant_id: uuid.UUID) -> Booking:
    """Retrieve a single booking by ID, raising NotFoundError if missing."""
    stmt = (
        select(Booking)
        .options(selectinload(Booking.slot))
        .where(Booking.id == booking_id, Booking.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    booking = result.scalars().first()
    if not booking:
        raise NotFoundError(f"Booking with ID {booking_id} not found.")
    return booking
