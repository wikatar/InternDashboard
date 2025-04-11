#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    # Create virtual environment if it doesn't exist
    python3 -m venv venv
    source venv/bin/activate
    # Install requirements only once
    pip install -r requirements.txt
fi

# Launch the Streamlit app
streamlit run app.py 