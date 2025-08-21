#!/bin/bash

# Kill any running Python processes
pkill -f 'python'

# Start the Flask application
python3 /Users/reddy/2025/PaperAgent/scripts/simple_pipeline_api.py
