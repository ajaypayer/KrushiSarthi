#!/usr/bin/env bash
# exit on error
set -o errexit

# Install production dependencies
pip install -r requirements.txt

# Compile static assets
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Populate the SQLite database with CSV datasets
python import_csv_to_sqlite.py
