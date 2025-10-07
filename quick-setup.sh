#!/bin/bash
# Quick WARP Manager Setup - Copy/Paste Friendly

echo "🚀 QUICK WARP MANAGER SETUP"
echo "============================="

# Install dependencies
pip install --break-system-packages zstandard keyring 2>/dev/null || echo "Dependencies already installed"

# Make executable
chmod +x warp-manager.py

# Create CLI alias
echo "alias warp-manager='$(pwd)/warp-manager.py'" >> ~/.bashrc
echo "alias warp-manager='$(pwd)/warp-manager.py'" >> ~/.zshrc

# Test functionality
echo ""
echo "✅ TESTING FUNCTIONALITY:"
echo "------------------------"
./warp-manager.py --help

echo ""
echo "🎯 READY TO USE:"
echo "----------------"  
echo "GUI:  ./warp-manager.py"
echo "CLI:  ./warp-manager.py --snapshot"
echo "List: ./warp-manager.py --list"
echo ""
echo "💾 Backups: ~/.warp-backups/"
echo "🌐 GitHub: https://github.com/EnkiJJK/warp-data-manager"
echo ""