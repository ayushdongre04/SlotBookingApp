import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.model import OutboxEvent


def enqueue_event(
    db: AsyncSession, tenant_id: uuid.UUID, event_type: str, payload: dict
) -> None:
    """Adds an OutboxEvent to the session — deliberately does NOT commit.
    The caller must call db.commit() itself, AFTER adding both the
    business-state change and this event to the same session. That's
    what makes them atomic.
    """
    db.add(OutboxEvent(tenant_id=tenant_id, event_type=event_type, payload=payload))
