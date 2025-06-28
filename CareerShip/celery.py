import os
from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CareerShip.settings')

app = Celery('CareerShip')
app.config_from_object('django.conf:settings', namespace='CELERY')

# This will make sure that the logger configured in settings.py is used
@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(['projects'])
