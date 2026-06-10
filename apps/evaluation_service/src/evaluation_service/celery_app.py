from celery import Celery

from evaluation_service.config import get_settings


def make_celery() -> Celery:
    settings = get_settings()
    app = Celery(
        "evaluation",
        broker=settings.broker_url,
        include=["evaluation_service.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )
    return app


celery_app = make_celery()
