import logging
import os

from celery import Celery
from django.conf import settings

logger = logging.getLogger('django')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample_crawler.settings')

app = Celery('sample_crawler', broker=settings.CELERY_BROKER)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
