#!/bin/bash
set -e

echo "🚀 Installing WARP Data Manager..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Do not run this script as root!"
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Create virtual environment
VENV_DIR="$HOME/.local/share/warp-manager-venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install zstandard keyring

# Make script executable
chmod +x warp-manager.py

# Create desktop entry
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/warp-manager.desktop" << EOF
[Desktop Entry]
Name=WARP Data Manager
Comment=Backup and manage WARP Terminal data
Exec=$VENV_DIR/bin/python $(pwd)/warp-manager.py
Icon=folder-sync
Terminal=false
Type=Application
Categories=Utility;System;
Keywords=warp;backup;terminal;
EOF

# Create CLI wrapper
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/warp-manager" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
exec python "$(dirname \$0)/../share/warp-manager/warp-manager.py" "\$@"
EOF

# Create share directory and copy files
SHARE_DIR="$HOME/.local/share/warp-manager"
mkdir -p "$SHARE_DIR"
cp warp-manager.py "$SHARE_DIR/"
chmod +x "$BIN_DIR/warp-manager"

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo "✅ WARP Data Manager installed successfully!"
echo ""
echo "🎯 Usage:"
echo "  GUI: Launch from applications menu or run 'warp-manager'"
echo "  CLI: Run 'warp-manager --help' for commands"
echo ""
echo "📍 Backups stored in: ~/.warp-backups"
echo ""