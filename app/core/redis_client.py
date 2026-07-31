import uuid

from redis.asyncio import Redis, from_url

from app.core.config import settings

# One shared connection pool for the entire application both publishing
# (from booking mutations) and subscribing (from SSE connections) reuse this,
# rather than opening a fresh connection per request.
redis_client: Redis = from_url(
    settings.redis_url, decode_responses=True, encoding="utf-8"
)


def slot_events_channel(tenant_id: uuid.UUID) -> str:
    """
    Channel name is tenant scoped because an SSE subscriber must never receive
    another tenant's events.
    """

    return f"slot-events:{tenant_id}"