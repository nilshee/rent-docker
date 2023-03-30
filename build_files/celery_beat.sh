#!/bin/sh
celery -A backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler