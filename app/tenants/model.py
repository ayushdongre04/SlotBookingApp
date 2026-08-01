import uuid
from datetime import datetime, UTC

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base


class Tenant(Base):
    """
    Represents a tenant in the system. Each tenant can have multiple users, providers and slots.
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC)
    )

    users: Mapped[list["User"]] = relationship(back_populates="tenant")