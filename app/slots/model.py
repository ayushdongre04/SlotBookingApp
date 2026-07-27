import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.providers.model import Provider


class SlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("providers.id"), nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus), default=SlotStatus.AVAILABLE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    provider: Mapped["Provider"] = relationship(back_populates="slots")
    # uselist=False indicates a one-to-one relationship, meaning each slot
    # can have at most one booking associated with it.
    # booking: Mapped["Booking"] = relationship(back_populates="slot", uselist=False)
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="slot",
    )