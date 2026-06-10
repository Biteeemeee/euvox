from celery import Celery

from surrogate_service.config import get_settings

_settings = get_settings()
celery_app = Celery("surrogate_service", broker=_settings.broker_url)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
