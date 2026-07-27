import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.slots.model import Slot


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        # Partial Index: Ensures that slot_id is unique for all bookings that are not cancelled.
        # Any status EXCEPT cancelled holds the slot (will remain unique).
        # Cancelling is the only action that frees slot_id up for a new booking.
        # Adding a new status later are treated as blocking by default.
        Index(
            "uq_booking_slot_active",
            "slot_id",
            unique=True,
            postgresql_where=text("status!='CANCELLED'"), # postgres store the BookingStatus Key names
            # postgresql_where=(status != BookingStatus.CANCELLED)
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("slots.id"), nullable=False
    )
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    slot: Mapped["Slot"] = relationship(back_populates="bookings")
