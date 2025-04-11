#!/usr/bin/env python3
"""
Direct launcher for Balthazar Dashboard
This script directly launches the Streamlit app with proper settings
"""

import os
import sys
import streamlit.web.cli as stcli
from pathlib import Path

# Set the matplotlib backend
os.environ['MPLBACKEND'] = 'Agg'

# Get the directory of this script
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Path to the app.py file
app_path = os.path.join(script_dir, "app.py")

if not os.path.exists(app_path):
    print(f"Error: Could not find app.py in {script_dir}")
    sys.exit(1)

print("="*50)
print("Balthazar Dashboard - Direct Launch")
print("="*50)
print(f"Working directory: {os.getcwd()}")
print(f"Launching app at: {app_path}")

# Launch Streamlit directly
sys.argv = ["streamlit", "run", app_path, "--server.headless", "true"]
sys.exit(stcli.main()) 