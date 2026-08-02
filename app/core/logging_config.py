import json
import logging
import sys
from datetime import datetime, timezone

from app.core.context import request_id_var


class JSONFormatter(logging.Formatter):
    """
    Emites one JSON object per line
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get()
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # anything passed via logger.info("msg", extra={"ctx_order_id": ...})
        for key, value in record.__dict__.items():
            if key.startswith("ctx_"):
                payload[key[4:]] = value
        return json.dumps(payload, default=str)

def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet the noisy libraries down to WARNING so your own logs aren't
    # drowned out by SQLAlchemy's per-query chatter in dev.
    # logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)