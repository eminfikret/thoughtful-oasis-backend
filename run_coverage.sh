#!/bin/bash

# Run tests with coverage
echo "Running tests with coverage..."
coverage run --source='.' manage.py test

# Generate coverage reports
echo "Generating coverage reports..."
coverage report
coverage html

CONTAINER_DIR=$(pwd)

echo "----------------------------------------"
echo "Coverage report generated!"
echo "Text report: above"
echo "HTML report: in htmlcov/ directory"
echo ""
echo "To view the HTML report, run one of the following:"
echo "  start htmlcov/index.html     # Windows"
echo "  open htmlcov/index.html      # Mac"
echo "  xdg-open htmlcov/index.html  # Linux"
echo "----------------------------------------"