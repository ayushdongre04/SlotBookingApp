import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from typing import List

from app.booking.schemas import BookingCreate
from app.core.exceptions import NotFoundError, ConflictError
from app.outbox.service import enqueue_event
from app.slots.model import Slot, SlotStatus
from app.booking.model import Booking, BookingStatus


logger = logging.getLogger(__name__)


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

    # Enqueue an outbox event for the booking confirmation. The outbox event is added
    # to the session but not committed yet. The caller must commit after adding both
    # the booking and the outbox event to ensure atomicity.
    enqueue_event(
        db,
        tenant_id=tenant_id,
        event_type="booking_confirmed",
        payload={
            "booking_id": str(booking.id),
            "slot_id": str(slot.id),
            "customer_email": booking.customer_email,
        },
    )

    await db.commit()
    await db.refresh(booking)

    # Booking already committed successfully at this point — neither of
    # the two calls below should be able to turn a successful booking
    # into a failed API response if Redis/Celery has an issue.

    logger.info(
        "Booking created successfully",
        extra={"ctx_booking_id": booking.id, "ctx_slot_id": slot.id},
    )

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

    enqueue_event(
        db,
        tenant_id=tenant_id,
        event_type="booking_cancelled",
        payload={
            "booking_id": str(booking.id),
            "slot_id": str(booking.slot.id),
            "customer_email": booking.customer_email,
        },
    )

    await db.commit()
    await db.refresh(booking)

    logger.info(
        f"Booking cancelled successfully",
        extra={"ctx_booking_id": booking.id, "ctx_slot_id": booking.slot.id},
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
