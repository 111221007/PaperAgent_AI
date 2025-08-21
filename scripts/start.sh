#!/bin/bash

# Install dependencies
pip install -r ../requirements.txt || pip install -r requirements.txt

# Kill any running Python processes
pkill -f 'python'

# Start the Flask application
python3 scripts/simple_pipeline_api.py
