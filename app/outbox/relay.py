import asyncio
import json
import logging
from datetime import datetime, UTC
import platform
import selectors

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.redis_client import redis_client, slot_events_channel
from app.core.db_session import AsyncSessionLocal
from app.booking.tasks import send_booking_confirmation, send_booking_cancellation
from app.outbox.model import OutboxEvent, OutboxEventStatus

logger = logging.getLogger(__name__)

BATCH_SIZE = 20
MAX_ATTEMPTS = 5


async def _dispatch(event: OutboxEvent) -> None:
    payload = event.payload

    if event.event_type == "booking_confirmed":
        send_booking_confirmation.delay(
            payload["booking_id"], payload["customer_email"]
        )
        await redis_client.publish(
            slot_events_channel(event.tenant_id),
            json.dumps({"slot_id": str(payload["slot_id"]), "status": "booked"}),
        )
    elif event.event_type == "booking_cancelled":
        send_booking_cancellation.delay(
            payload["booking_id"], payload["customer_email"]
        )
        await redis_client.publish(
            slot_events_channel(event.tenant_id),
            json.dumps({"slot_id": str(payload["slot_id"]), "status": "available"}),
        )
    else:
        raise ValueError(f"Unknown outbox event_type: {event.event_type}")


async def _process_batch() -> dict:
    # FOR UPDATE SKIP LOCKED: if this relay ever runs as more than
    # one process/replica, two relays racing for the same batch
    # don't block each other OR double-process the same row.
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxEventStatus.PENDING)
            .order_by(OutboxEvent.created_at)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        events = result.scalars().all()

        processed, failed = 0, 0
        for event in events:
            try:
                await _dispatch(event)
                event.status = OutboxEventStatus.PROCESSED
                event.processed_at = datetime.now(UTC)
                processed += 1
            except Exception as exc:
                event.attempts += 1
                event.last_error = str(exc)[:500]
                if event.attempts >= MAX_ATTEMPTS:
                    event.status = OutboxEventStatus.FAILED
                    logger.error(
                        "outbox event exceeded max attempts, giving up",
                        extra={
                            "ctx_event_id": str(event.id),
                            "ctx_event_type": event.event_type,
                        },
                    )
                    failed += 1
                else:
                    logger.warning(
                        "outbox event dispatch failed, will retry",
                        extra={
                            "ctx_event_id": str(event.id),
                            "ctx_attempts": event.attempts,
                            "ctx_error": str(exc),
                        },
                    )
        await db.commit()
        return {"processed": processed, "failed": failed, "total": len(events)}

def run_async(coro):
    """
    Run an async coroutine in a synchronous context, handling Windows event loop policy.
    This is necessary because Celery tasks run synchronously by default, and we need to bridge
    into async DB/Redis calls. This function ensures that the appropriate event loop policy is
    set for Windows, which requires a different event loop implementation.
    """
    if platform.system() == "Windows":
        return asyncio.run(
            coro,
            loop_factory=lambda: asyncio.SelectorEventLoop(
                selectors.SelectSelector()
            ),
        )

    return asyncio.run(coro)

@celery_app.task(name="outbox.process_events")
def process_outbox_events():
    """Celery task — scheduled entrypoint for the relay. A SYNC function
    bridging into async DB/Redis calls via asyncio.run(), since Celery
    tasks run synchronously by default."""
    result = run_async(_process_batch())
    if result["total"] > 0:
        logger.info(
            "outbox relay batch complete",
            extra={f"ctx_{k}": v for k, v in result.items()},
        )
    return result
