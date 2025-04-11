#!/bin/zsh

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

# Make a temporary launch file
cat > ~/Desktop/temp_launch.command << 'EOL'
#!/bin/zsh
cd "$(dirname "$0")"/../"The Balthazar Project/InternDashboard"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python 3 first."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install requirements if needed
pip install -r requirements.txt

# Launch the app
streamlit run app.py
EOL

# Make it executable
chmod +x ~/Desktop/temp_launch.command

# Open it
open ~/Desktop/temp_launch.command

echo "Dashboard launcher created on your Desktop. You can now run it anytime." 