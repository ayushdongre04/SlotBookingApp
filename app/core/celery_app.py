from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "slotbooking",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)

# Auto-discover @celery_app.task-decorated functions in feature folders so
# new features don't need a manual import registered here.
# autodiscover_tasks only looks for a module literally named "tasks.py"
# inside each listed package
celery_app.autodiscover_tasks(["app.booking"])

# relay.py doesn't match the "tasks.py" naming convention autodiscover
# expects, so it's imported explicitly here instead
from app.outbox import relay  # noqa: F401,E402

# The outbox relay runs on a fixed schedule via Celery beat, independent
# of any request — it turns durably-recorded OutboxEvent rows into real
# Celery dispatches and Redis publishes.
# CDC (Change Data Capture) with tools like Debezium: Streams database
# changes directly to Kafka or another broker without polling.
celery_app.conf.beat_schedule = {
    "process-outbox-events": {
        "task": "outbox.process_events",
        "schedule": 5.0,
    },
}