#!/bin/bash
set -e

# Run migrations
alembic upgrade head 

uv run -m data.load_stock_data

uv run -m uvicorn main:app --port 8000