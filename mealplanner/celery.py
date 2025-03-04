from __future__ import absolute_import, unicode_literals
import os
from celery.schedules import crontab
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mealplanner.settings')

app = Celery('mealplanner')


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mealplanner.settings')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    # Other scheduled tasks...
    'send-scheduled-notifications': {
        'task': 'meals.tasks.send_scheduled_notifications',
        'schedule': crontab(minute='0', hour='9'),  # Run daily at 9 AM
    },
}