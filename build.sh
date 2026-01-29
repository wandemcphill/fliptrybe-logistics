#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip to ensure the latest pathing logic
pip install --upgrade pip

# Install dependencies (This installs gunicorn and psycopg2-binary)
pip install -r requirements.txt

# Run migrations to build the database on Render
flask --app wsgi db upgrade