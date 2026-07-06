#!/bin/sh
set -e
celery -A app.core.celery_app.celery_app beat --loglevel=info
