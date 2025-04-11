#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install requirements if not already installed
pip install -r requirements.txt

# Launch the Streamlit app
streamlit run app.py 