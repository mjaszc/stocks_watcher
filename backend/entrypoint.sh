#!/bin/bash
set -e

# Run migrations
alembic upgrade head 

uv run -m data.load_stock_data

fastapi run main.py --port 8000