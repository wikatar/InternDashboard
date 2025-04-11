#!/bin/bash

# Create the app bundle directory structure
mkdir -p "Balthazar Dashboard.app/Contents/MacOS"
mkdir -p "Balthazar Dashboard.app/Contents/Resources"

# Create the Info.plist file
cat > "Balthazar Dashboard.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>dashboard</string>
    <key>CFBundleIdentifier</key>
    <string>com.balthazar.dashboard</string>
    <key>CFBundleName</key>
    <string>Balthazar Dashboard</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>
EOF

# Create the executable script
cat > "Balthazar Dashboard.app/Contents/MacOS/dashboard" << EOF
#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"
cd "\$SCRIPT_DIR/../../../"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install requirements if not already installed
pip install -r requirements.txt

# Launch the Streamlit app
streamlit run app.py
EOF

# Make the executable script executable
chmod +x "Balthazar Dashboard.app/Contents/MacOS/dashboard"

echo "App bundle created successfully!"
echo "You can now drag 'Balthazar Dashboard.app' to your Applications folder or Dock." 