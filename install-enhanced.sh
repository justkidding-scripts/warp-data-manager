#!/bin/bash
set -e

echo "🚀 Installing WARP Data Manager Enhanced v1.2.0..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Do not run this script as root!"
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --break-system-packages zstandard keyring requests schedule

# Make scripts executable
chmod +x warp-manager.py warp-manager-enhanced.py

# Create systemd user directory
mkdir -p ~/.config/systemd/user

# Install systemd service for scheduler
sed "s|/home/kali|$HOME|g" warp-backup-scheduler.service > ~/.config/systemd/user/warp-backup-scheduler.service

# Create desktop entries
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

# Basic WARP Manager desktop entry
cat > "$DESKTOP_DIR/warp-manager.desktop" << EOF
[Desktop Entry]
Name=WARP Data Manager
Comment=Backup and manage WARP Terminal data
Exec=$(pwd)/warp-manager.py
Icon=folder-sync
Terminal=false
Type=Application
Categories=Utility;System;
Keywords=warp;backup;terminal;
EOF

# Enhanced WARP Manager desktop entry
cat > "$DESKTOP_DIR/warp-manager-enhanced.desktop" << EOF
[Desktop Entry]
Name=WARP Data Manager Enhanced
Comment=Advanced WARP backup with GitHub sync and scheduling
Exec=$(pwd)/warp-manager-enhanced.py
Icon=folder-cloud
Terminal=false
Type=Application
Categories=Utility;System;Network;
Keywords=warp;backup;github;scheduler;
EOF

# Create CLI wrappers
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/warp-manager" << EOF
#!/bin/bash
exec "$(pwd)/warp-manager.py" "\$@"
EOF

cat > "$BIN_DIR/warp-manager-enhanced" << EOF
#!/bin/bash
exec "$(pwd)/warp-manager-enhanced.py" "\$@"
EOF

chmod +x "$BIN_DIR/warp-manager" "$BIN_DIR/warp-manager-enhanced"

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# Enable systemd user services
systemctl --user daemon-reload
systemctl --user enable warp-backup-scheduler.service

echo "✅ WARP Data Manager Enhanced installed successfully!"
echo ""
echo "🎯 Available Tools:"
echo "  Basic GUI:     warp-manager"
echo "  Enhanced GUI:  warp-manager-enhanced"
echo "  Basic CLI:     warp-manager --help"
echo "  Enhanced CLI:  warp-manager-enhanced --help"
echo ""
echo "🔧 GitHub Setup:"
echo "  warp-manager-enhanced --setup-github"
echo ""
echo "⏰ Scheduler:"
echo "  Daily:   warp-manager-enhanced --schedule daily --schedule-time 02:00"
echo "  Weekly:  warp-manager-enhanced --schedule weekly --schedule-time 03:00"
echo "  Start:   systemctl --user start warp-backup-scheduler.service"
echo "  Status:  systemctl --user status warp-backup-scheduler.service"
echo ""
echo "📍 Backups stored in: ~/.warp-backups"
echo "🌐 GitHub repo: https://github.com/EnkiJJK/warp-data-manager"
echo ""