#!/bin/bash
# WARP Manager Ultra-Fast Deploy - Copy/Paste Ready

echo "⚡ ULTRA-FAST WARP MANAGER DEPLOYMENT"
echo "===================================="

# Quick dependency install
pip install --break-system-packages zstandard requests schedule 2>/dev/null

# Test basic functionality
echo ""
echo "🧪 TESTING CORE FUNCTIONS:"
./warp-manager.py --list
./warp-manager-enhanced.py --list

echo ""
echo "📸 CREATING TEST SNAPSHOT:"
./warp-manager-enhanced.py --snapshot

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================="
echo ""
echo "🎯 READY TO USE:"
echo "----------------"
echo "Basic:     ./warp-manager.py --help"
echo "Enhanced:  ./warp-manager-enhanced.py --help"
echo ""
echo "🔥 QUICK COMMANDS:"
echo "-----------------"
echo "Snapshot:  ./warp-manager-enhanced.py --snapshot"
echo "Rules:     ./warp-manager-enhanced.py --backup rules"
echo "MCP:       ./warp-manager-enhanced.py --backup mcp"
echo "List:      ./warp-manager-enhanced.py --list"
echo ""
echo "🔧 GITHUB SETUP:"
echo "----------------"
echo "./warp-manager-enhanced.py --setup-github"
echo ""
echo "⏰ AUTOMATION:"
echo "-------------"
echo "Daily:     ./warp-manager-enhanced.py --schedule daily"
echo "Start:     ./warp-manager-enhanced.py --start-scheduler"
echo ""
echo "🌐 Repository: https://github.com/EnkiJJK/warp-data-manager"
echo "📂 Backups:   ~/.warp-backups/"
echo ""