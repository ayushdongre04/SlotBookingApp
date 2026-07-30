import logging
import uuid

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def send_booking_confirmation(self, booking_id: uuid.UUID, customer_email: str):
    """Runs in a separate Celery worker process — NOT in the request
    path. A failure here retries up to 3 times before giving up — it
    never blocks or fails the booking API call itself, since it's
    enqueued asynchronously after the DB commit already succeeded.
    """
    try:
        logger.info(
            "sending booking confirmation",
            extra={"ctx_booking_id": booking_id, "ctx_customer_email": customer_email},
        )
    except Exception as e:
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def send_booking_cancellation(self, booking_id: str, customer_email: str):
    try:
        logger.info(
            "sending booking cancellation notice",
            extra={"ctx_booking_id": booking_id, "ctx_customer_email": customer_email},
        )
    except Exception as e:
        raise self.retry(exc=e)
