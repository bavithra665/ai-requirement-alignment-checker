#!/usr/bin/env bash
# exit on error
set -o errexit

# Install uv (fast python package installer)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Install dependencies via uv pip
uv pip install --system -e .

# Run database migrations
python manage.py migrate

# Collect static files (if needed by Django admin)
# python manage.py collectstatic --no-input
