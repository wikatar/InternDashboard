#!/usr/bin/env python3
import os
import subprocess
import sys
import site
from pathlib import Path
import time

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    print("Starting Balthazar Dashboard...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    
    # Check if running in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("Running in virtual environment")
    else:
        print("Running in system Python")
    
    # Set matplotlib backend before importing other modules
    try:
        # This needs to be done before importing matplotlib.pyplot
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        print(f"Set matplotlib backend to: {matplotlib.get_backend()}")
    except ImportError:
        print("Warning: Could not set matplotlib backend")
    
    # Check for streamlit
    try:
        import streamlit
        print(f"Streamlit is already installed (version: {streamlit.__version__})")
    except ImportError:
        print("Installing requirements...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("Requirements installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")
            return
    
    # Verify other key packages are installed
    try:
        import pandas as pd
        print(f"Pandas version: {pd.__version__}")
        
        import matplotlib.pyplot as plt
        print(f"Matplotlib version: {matplotlib.__version__}")
        
        import seaborn as sns
        print(f"Seaborn version: {sns.__version__}")
        
        import gspread
        print(f"gspread version: {gspread.__version__}")
        
        import plotly
        print(f"Plotly version: {plotly.__version__}")
    except ImportError as e:
        print(f"Warning: Could not import a required package: {e}")
        print("Installing requirements again to ensure all dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")
            return
    
    # Check if app.py exists
    if not os.path.exists("app.py"):
        print("Error: app.py not found in the current directory")
        return
    
    # Launch the app
    print("Launching dashboard...")
    try:
        # Set environment variable for matplotlib
        os.environ['MPLBACKEND'] = 'Agg'
        process = subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
        print(f"Dashboard process completed with exit code {process.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"Error launching dashboard: {e}")
    except KeyboardInterrupt:
        print("Dashboard process was interrupted by user")

if __name__ == "__main__":
    main() 