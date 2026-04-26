from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    "anyalert_parser",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.rozetka"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Kiev",
    enable_utc=True,
    beat_schedule={
        'check-rozetka-every-30-mins': {
            'task': 'app.tasks.rozetka.fetch_and_parse_all',
            'schedule': crontab(minute='*/30'),
        },
    }
)
