import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.booking import service
from app.booking.schemas import BookingResponse, BookingCreate
from app.core.db_session import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=List[BookingResponse])
async def get_all_bookings(
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch all bookings.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
    Returns:
        List[BookingResponse]: A list of all bookings.
    """
    bookings = await service.get_all_bookings(db)
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_by_id(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch a booking by ID.
    Args:
        booking_id (uuid.UUID): The ID of the booking to fetch.
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
    Returns:
        BookingResponse: The booking instance.
    """
    booking = await service.get_booking_by_id(db, booking_id)
    return booking


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    payload: BookingCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new booking.
    Args:
        payload (BookingResponse): The schema containing the booking data to create.
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
    Returns:
        BookingResponse: The newly created booking instance.
    """
    booking = await service.create_booking(db, payload)
    return booking


@router.delete("/{booking_id}", response_model=BookingResponse)
async def cancel_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an existing booking.
    Args:
        booking_id (uuid.UUID): The ID of the booking to cancel.
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
    Returns:
        BookingResponse: The canceled booking instance.
    """
    booking = await service.cancel_booking(db, booking_id)
    return booking
