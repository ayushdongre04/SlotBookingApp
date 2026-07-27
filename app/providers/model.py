import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )
    # "Slot" is a string forward-reference — resolved by SQLAlchemy's
    # mapper registry at configure time, so this file does NOT import
    # from app.slots. That's what keeps providers -> slots a
    # dependency that doesn't exist, only slots -> providers does.
    slots: Mapped[list["Slot"]] = relationship(back_populates="provider")