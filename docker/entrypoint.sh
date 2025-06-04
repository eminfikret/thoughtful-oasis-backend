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

if [ "${SEED_DATABASE}" = "true" ]; then
    echo "Seeding database with test data..."
    # Check if seed command exists
    if python manage.py help seed > /dev/null 2>&1; then
        python manage.py seed --channels=10 --posts=20 --comments=5 --votes=15 --subscriptions=3
        echo "Database seeding completed."
    else
        echo "Error: 'seed' command not found. Make sure the management app is properly installed."
        echo "Available commands:"
        python manage.py help
    fi
fi

# Start server
echo "Starting server"
exec "$@"