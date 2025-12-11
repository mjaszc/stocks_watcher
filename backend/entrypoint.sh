#!/bin/bash
set -e

# Run migrations
alembic upgrade head 
echo "Migrations complete. Starting application server..."

exec fastapi run --port 8000 --workers 4 main.py
