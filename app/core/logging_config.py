"""
Structured JSON logging for production.
In development plain text logs are used for readability.
"""
import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configure root logger — JSON in production, plain text in dev."""

    if settings.ENVIRONMENT == "production":
        from pythonjsonlogger.json import JsonFormatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
        ))
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
