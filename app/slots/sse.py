import logging
from collections.abc import AsyncGenerator
import uuid

from fastapi import Request

from app.core.redis_client import redis_client, slot_events_channel

logger = logging.getLogger(__name__)

# How often to send a keep-alive comment when no real event has fired.
# Needed because many reverse proxies / load balancers silently close
# connections that sit idle for ~30-60s with no bytes sent — an SSE
# comment line (": keep-alive\n\n") resets that idle timer without the
# client's JS ever seeing it as a real event.
KEEPALIVE_INTERVAL_SECONDS = 15


async def slot_events_stream(request: Request, tenant_id: uuid.UUID) -> AsyncGenerator[str, None]:
    """
    Yields Server-Sent Events for slot availability changes, scoped to
    one tenant. Subscribes to this tenant's Redis Pub/Sub channel so it
    receives events published from ANY worker process, not just the one
    handling this connection.
    """
    pubsub = redis_client.pubsub()
    channel = slot_events_channel(tenant_id=tenant_id)
    await pubsub.subscribe(channel)

    try:
        yield "event: connected\ndata: {}\n\n"

        while True:
            # request.is_disconnected(): to know whether browser closed tab
            if await request.is_disconnected():
                logger.info("SSE client disconnected", extra={"ctx_tenant_id": str(tenant_id)})
                break

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=KEEPALIVE_INTERVAL_SECONDS
            )

            if message is None:
                # In SSE colon means comment - browser never exposes it.
                yield ": keep-alive\n\n"
                continue

            yield f"event: slot_update\ndata: {message['data']}\n\n"
    except Exception:
        logger.error(
            "SSE stream failed",
            exc_info=True,
            extra={"ctx_tenant_id": str(tenant_id)},
        )
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()