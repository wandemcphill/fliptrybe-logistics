#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations to build the database on Render
flask db upgrade

# Optional: Seed the database if you want it done automatically
# python seed_all.py