import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Drag_skupkabot.settings')
celery_app = Celery('Drag_skupkabot')

celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()
celery_app.conf.result_expires = 60*2
celery_app.conf.beat_schedule = {
    'set_daily_stats': {
        'task': 'tgbot.tasks.check_participants',
        'schedule': crontab(minute='59', hour='23')}

}

celery_app.conf.timezone = 'UTC'
