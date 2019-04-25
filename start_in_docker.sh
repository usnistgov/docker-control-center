#!/bin/bash

# Exit if any of following commands fails
set -e

# Create settings.py and generate key if it doesn't exist already
if [[ ! -e /control-center/config/settings.py ]]; then
    echo "SECRET_KEY='$(python3.6 -c 'from django.core.management.utils import get_random_secret_key;print(get_random_secret_key())')'" > /control-center/config/settings.py
fi

# Run migrations to create or update the database
django-admin migrate

# Collect static files
django-admin collectstatic --no-input --clear

# Run Control Center
gunicorn --config=/etc/gunicorn_configuration.py control_center.wsgi:application