#!/usr/bin/env python3
"""
Simple launcher for the Balthazar Dashboard.
Run this script directly with Python to launch the dashboard.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    print("="*50)
    print("Balthazar Dashboard Launcher")
    print("="*50)
    print(f"Working directory: {os.getcwd()}")
    
    # Set environment variable for matplotlib
    os.environ['MPLBACKEND'] = 'Agg'
    
    # Find the run_dashboard.py script
    if os.path.exists("run_dashboard.py"):
        run_script = "run_dashboard.py"
    elif os.path.exists("app.py"):
        run_script = "app.py"
    else:
        print("Error: Cannot find dashboard scripts.")
        return
    
    # Execute the dashboard
    try:
        if run_script == "run_dashboard.py":
            print("Launching with run_dashboard.py...")
            process = subprocess.run([sys.executable, run_script], check=True)
        else:
            print("Launching app.py directly with streamlit...")
            # First try to ensure streamlit is installed
            subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"], check=False)
            process = subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
        
        print(f"Dashboard process completed with exit code {process.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"Error launching dashboard: {e}")
    except KeyboardInterrupt:
        print("Dashboard process was interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 