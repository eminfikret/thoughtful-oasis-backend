#!/bin/bash
coverage run --source='.' manage.py test
coverage report
coverage html
echo "HTML coverage report generated in htmlcov/ directory"