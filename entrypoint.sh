#!/bin/sh
python manage.py migrate  --noinput
echo "database migrated"
python manage.py collectstatic --noinput
echo "static files collected"

# Check if arguments are passed
if [ -z "$1" ]; then
  echo "No command provided. Running default command..."
  gunicorn CareerShip.wsgi -b 0.0.0.0:8001 --disable-redirect-access-to-syslog --timeout 200 --reload
else
  # Execute the passed command
  exec "$@"
fi
