"""
Structured logging configuration.

Configures a single named logger ("llm_backend") used throughout the app.
Call sites pass structured context via the `extra=` parameter. A filter
automatically attaches the current request's correlation ID (from
main.py's RequestIDMiddleware) to every log record.

NEVER log api keys, authorization headers, or raw request bodies --
only pass specific, deliberately-chosen safe fields.
"""

import logging
import sys

from app.core.config import settings

logger = logging.getLogger("llm_backend")


class RequestIDLogFilter(logging.Filter):
    """Attaches the current request's correlation ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Imported here (not at module level) to avoid a circular import,
        # since main.py imports from this module too.
        from app.main import request_id_var

        record.request_id = request_id_var.get()
        return True


def configure_logging() -> None:
    """Set up logging. Call once, at app startup (see main.py)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | [%(request_id)s] | %(message)s")
    )
    handler.addFilter(RequestIDLogFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(handler)