#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn --bind=0.0.0.0:8000 --timeout 600 news_api.wsgi
