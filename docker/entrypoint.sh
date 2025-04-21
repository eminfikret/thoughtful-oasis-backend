#!/bin/bash

# Wait for postgres
echo "Waiting for postgres..."
sleep 5

# Apply database migrations
python manage.py migrate

# Create a superuser if it doesn't exist
python manage.py shell << END
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser created.")
else:
    print("Superuser already exists.")

# Create a demo user if it doesn't exist
if not User.objects.filter(username='demo').exists():
    User.objects.create_user('demo', 'demo@example.com', 'demo123')
    print("Demo user created.")
else:
    print("Demo user already exists.")
END

# Start server
echo "Starting server"
exec "$@"