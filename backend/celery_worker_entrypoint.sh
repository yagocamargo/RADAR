#!/bin/sh
set -e
celery -A app.core.celery_app.celery_app worker --loglevel=info --concurrency=2
