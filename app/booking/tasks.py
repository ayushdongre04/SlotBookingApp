import logging
import uuid

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

# bind=True allows the task to access its own state and methods, such as retry()
# max_retries=3 allows the task to be retried up to 3 times in case of failure
# default_retry_delay=10 sets the delay between retries to 10 seconds
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
        # Celery's retry mechanism allows the task to be retried in case of failure.
        # The `exc` parameter is used to pass the exception that caused the failure,
        # which can be useful for logging and debugging purposes.
        # The `self.retry()` method raises a `Retry` exception, which tells Celery
        # to retry the task after the specified delay. If the maximum number of retries is reached,
        # the task will be marked as failed.
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
