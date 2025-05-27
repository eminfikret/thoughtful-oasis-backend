# Fact Checking API Backend

## Overview
A backend API service for fact checking operations.

## Setup

1. Create a `.env` file in the `/docker` directory if it does not already exist.

## Running the Application
Navigate to the `/docker` folder and run:
```bash
docker compose up --build -d
```

## Development

### API Documentation
Once the application is running, navigate to `localhost:8000/swagger` to access the interactive Swagger API documentation.

### Seeded Users
The application comes with pre-configured users for testing:

| Type  | Username | Password | Email             | Role                               |
|-------|----------|----------|-------------------|-----------------------------------|
| Admin | admin    | admin    | admin@example.com | Superuser (access to Django admin) |
| Demo  | demo     | demo123  | demo@example.com  | Regular user                       |

The Django admin panel is available at `localhost:8000/admin`.


### Testing
This project consists of tests for each module. To run all tests, navigate to the `/docker` folder and run:
```bash
docker compose exec app python manage.py test
```

### Linting
This project uses Ruff for Python code linting. To run linting checks, navigate to the `/docker` folder and run:

```bash
docker-compose -f docker-compose.yml run --rm lint
```

For automatic fixing of some issues, run:
```bash
docker-compose -f docker-compose.yml run --rm lint ruff check --fix .
```