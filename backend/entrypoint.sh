#!/bin/bash
set -e

# Run migrations
alembic upgrade head 

# uv run -m uvicorn main:app
fastapi run --port 8000 --workers 4 main.py
