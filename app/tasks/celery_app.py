"""
Celery application instance.

Broker and result backend are both driven by REDIS_URL from app settings,
so changing the Redis connection in .env automatically applies here.
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "blood_donor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.matching_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # When CELERY_TASK_ALWAYS_EAGER=True tasks run synchronously in the same
    # process — no broker needed.  Set in .env for local dev without Redis.
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=settings.CELERY_TASK_ALWAYS_EAGER,
)
