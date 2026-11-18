# Fact Checking API Backend

## Overview
A backend API service for fact checking operations.

## Setup

1. Create a `.env` file inside the `/docker` directory (if it doesn't already exist).
2. Add the following environment variables:

Example `.env` file:

```env
DJANGO_SECRET_KEY=your_django_secret_key
POSTGRES_DB=fact_check_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/1
WIKIPEDIA_API_URL=http://your-server-host/wikipedia/search
LLM_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=your_api_key
BACKEND_API_URL=http://localhost:8000/api/v1
```

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

### Test Coverage
The project includes a coverage reporting tool to measure test coverage. To run tests with coverage reporting:

```bash
docker compose exec app ./run_coverage.sh
```

This generates:
- A terminal output showing coverage statistics
- An HTML report for detailed line-by-line coverage analysis

To view the HTML coverage report, open `htmlcov/index.html` in a web browser:

```bash
start htmlcov/index.html  # Windows
# or
open htmlcov/index.html   # Mac
# or
xdg-open htmlcov/index.html  # Linux
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