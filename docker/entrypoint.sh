#!/bin/bash

# Wait for postgres
echo "Waiting for postgres..."
sleep 5

# Apply database migrations
python manage.py migrate

# Create a superuser if it doesn't exist
python manage.py shell << END
from django.contrib.auth.models import User
from users.models import UserProfile

# Create admin user
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser created.")
else:
    admin_user = User.objects.get(username='admin')
    print("Superuser already exists.")

# Create admin user profile
if not UserProfile.objects.filter(user=admin_user).exists():
    UserProfile.objects.create(user=admin_user, bio="Admin user profile", website="https://admin.com")
    print("Admin user profile created.")
else:
    print("Admin user profile already exists.")

# Create demo user
if not User.objects.filter(username='demo').exists():
    demo_user = User.objects.create_user('demo', 'demo@example.com', 'demo123')
    print("Demo user created.")
else:
    demo_user = User.objects.get(username='demo')
    print("Demo user already exists.")

# Create demo user profile
if not UserProfile.objects.filter(user=demo_user).exists():
    UserProfile.objects.create(user=demo_user, bio="Demo user profile", website="https://demo.com")
    print("Demo user profile created.")
else:
    print("Demo user profile already exists.")
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
exec python manage.py runserver 0.0.0.0:8000