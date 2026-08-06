import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.model import OutboxEvent, OutboxEventStatus


def enqueue_event(
    db: AsyncSession, tenant_id: uuid.UUID, event_type: str, payload: dict
) -> None:
    """Adds an OutboxEvent to the session — deliberately does NOT commit.
    The caller must call db.commit() itself, AFTER adding both the
    business-state change and this event to the same session. That's
    what makes them atomic.
    """
    db.add(
        OutboxEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload
        )
    )


async def get_pending_batch_for_update(db: AsyncSession, limit: int) -> list[OutboxEvent]:
    """FOR UPDATE SKIP LOCKED: if the relay ever runs as more than one
    process/replica, two relays racing for the same batch don't block
    each other OR double-process the same row."""
    result = await db.execute(
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxEventStatus.PENDING)
        .order_by(OutboxEvent.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list(result.scalars().all())