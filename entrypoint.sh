#!/bin/sh
python manage.py migrate  --noinput
echo "database migrated"
gunicorn CareerShip.wsgi -b 0.0.0.0:8001 --disable-redirect-access-to-syslog --timeout 200 --reload
