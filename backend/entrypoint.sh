#!/bin/bash
set -e

# Run migrations
alembic upgrade head 

# uv run -m uvicorn main:app
fastapi run --workers 4 main.py
