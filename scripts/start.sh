#!/bin/bash
# Kill any process running on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Start the Flask application using gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 simple_pipeline_api:app
