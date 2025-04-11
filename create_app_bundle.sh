#!/bin/bash

# Create the app bundle directory structure
mkdir -p "Balthazar Dashboard.app/Contents/MacOS"
mkdir -p "Balthazar Dashboard.app/Contents/Resources"

# Copy the icon (if you have one)
# cp icon.icns "Balthazar Dashboard.app/Contents/Resources/"

# Create the Info.plist file
cat > "Balthazar Dashboard.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>BalthazarDashboard</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
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
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

# Create the executable script
cat > "Balthazar Dashboard.app/Contents/MacOS/BalthazarDashboard" << EOF
#!/bin/bash
SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"
cd "\$SCRIPT_DIR/../../../"
osascript BalthazarDashboard.applescript
EOF

# Make the executable script executable
chmod +x "Balthazar Dashboard.app/Contents/MacOS/BalthazarDashboard"
chmod +x launch_dashboard.sh

echo "App bundle created successfully!"
echo "You can now drag 'Balthazar Dashboard.app' to your Applications folder or Dock." 