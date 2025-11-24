#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn --bind=0.0.0.0:8000 \
  --workers=1 \
  # Using 1 worker because SSE Pub/Sub is in-memory. Use Redis for >1 workers.
  --worker-class=gevent \
  --worker-connections=1000 \
  --timeout 600 \
  --graceful-timeout 30 \
  --keep-alive 75 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  news_api.wsgi
