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