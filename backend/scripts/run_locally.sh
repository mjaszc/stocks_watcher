#!/bin/sh

# This 'trap' command ensures that when you hit Ctrl+C, 
# it kills all the background processes (FastAPI, Celery, Node) at once.
trap "kill 0" EXIT

# 1. Start FastAPI (Current directory)
(cd ../ && ENVIRONMENT=local PYTHONPATH=$PWD fastapi dev main.py) &

# 2. Start Celery Worker (In parent directory)
# We use ( ) to change directory only for this specific command
(cd ../ && celery -A data.tasks worker) &

# 3. Start Celery Beat (In parent directory)
(cd ../ && celery -A data.tasks beat -l info) &

# 4. Start Frontend
# Moves up one level (cd ..), then moves to frontend (cd ../frontend)
(cd ../ && cd ../frontend && npm run dev) &

# This keeps the script running so the background tasks don't close immediately
wait