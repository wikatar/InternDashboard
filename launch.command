#!/bin/zsh

# Get the directory where this script is located
cd "$(dirname "$0")"

# Show a message
echo "===================================="
echo "  Launching Balthazar Dashboard"
echo "===================================="

# Run the Python launcher script
python3 launch.py 