#!/bin/bash
# Kill any process running on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
python simple_pipeline_api.py
