#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn --bind=0.0.0.0:8000 --workers=3 --worker-class=gevent --timeout 600 --graceful-timeout 30 news_api.wsgi
