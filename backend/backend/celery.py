import os

# from base import models

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

# use everythin with CELERY as prefix in backend/backend/settings.py as config for celery reference= https://docs.celeryq.dev/en/stable/userguide/configuration.html
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks
app.autodiscover_tasks()
