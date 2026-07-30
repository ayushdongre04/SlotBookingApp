from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "slotbooking",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serilizer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)

# Auto-discover @celery_app.task-decorated functions in feature folders so
# new features don't need a manual import registered here.
celery_app.autodiscover_tasks(["app.booking"])