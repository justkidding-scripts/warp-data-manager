# 🚀 WARP Data Manager

**Professional WARP Terminal Backup & Management Solution**

[![GitHub Stars](https://img.shields.io/github/stars/EnkiJJK/warp-data-manager?style=flat-square)](https://github.com/EnkiJJK/warp-data-manager)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey?style=flat-square)](#cross-platform-support)

> 🎯 **One-click backup, GitHub sync, automated scheduling for all your WARP Terminal data**

---

## 📦 **Quick Deploy (30 Seconds)**

```bash
# Clone and deploy in one command
git clone https://github.com/EnkiJJK/warp-data-manager.git && cd warp-data-manager && ./deploy-fast.sh
```

**That's it!** ✨ Your WARP backups are ready to use.

---

## 🎯 **What This Does**

WARP Data Manager automatically backs up **ALL** your WARP Terminal data:

- 🛡️ **WARP Rules** - Your AI assistant configurations
- ⚙️ **MCP Servers** - Model Context Protocol setups  
- 🗄️ **Databases** - All WARP Terminal databases
- ⚡ **Preferences** - Your settings and configurations
- 📝 **Logs** - Application logs and history
- 👤 **Profiles** - User profiles and customizations

**Plus** advanced features like GitHub sync, automated scheduling, and safe data reset!

---

## ⚡ **Two Versions Available**

| Version | Features | Best For |
|---------|----------|----------|
| **Basic v1.1.1** | Core backup, restore, GUI/CLI | Individual users, simple backups |
| **Enhanced v1.2.0** | + GitHub sync, automation, scheduling | Power users, teams, automated workflows |

---

## 🛠️ **Installation Options**

### Option 1: Ultra-Fast Deploy ⚡
```bash
git clone https://github.com/EnkiJJK/warp-data-manager.git
cd warp-data-manager
./deploy-fast.sh
```

### Option 2: Basic Installation 🔧
```bash
./install.sh
```

### Option 3: Enhanced (GitHub + Automation) 🚀
```bash
./install-enhanced.sh
```

### Option 4: Manual Setup 🔨
```bash
pip install zstandard requests schedule
chmod +x *.py
```

---

## 🎮 **Common Usage Examples**

### **📸 Quick Backup Commands**

```bash
# Take complete snapshot of everything
./warp-manager-enhanced.py --snapshot

# Backup only your WARP rules
./warp-manager-enhanced.py --backup rules

# Backup MCP servers and databases
./warp-manager-enhanced.py --backup mcp database

# Backup everything and upload to GitHub
./warp-manager-enhanced.py --snapshot --upload
```

### **📋 List & Manage Backups**

```bash
# List all local backups
./warp-manager-enhanced.py --list

# List backups on GitHub
./warp-manager-enhanced.py --list-remote

# Upload all local backups to GitHub
./warp-manager-enhanced.py --sync-all
```

### **🔄 Restore Operations**

```bash
# Restore from a specific backup (GUI version)
./warp-manager.py

# CLI restore (auto-creates safety backup first)
./warp-manager.py --restore ~/.warp-backups/backup-file.tar.zst
```

### **⚠️ Data Management**

```bash
# Delete WARP database (creates backup first)
./warp-manager.py --delete-db

# Safe reset all WARP data (moves to quarantine)
./warp-manager.py --reset
```

---

## ☁️ **GitHub Integration Setup**

### **Step 1: Get GitHub Token**
1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`
4. Copy the token

### **Step 2: Setup Integration**
```bash
./warp-manager-enhanced.py --setup-github
# Enter your token and username when prompted
```

### **Step 3: Start Backing Up to GitHub**
```bash
# Single backup with upload
./warp-manager-enhanced.py --backup rules --upload

# Upload all existing backups
./warp-manager-enhanced.py --sync-all
```

---

## ⏰ **Automated Scheduling**

### **Setup Automated Backups**

```bash
# Daily backup at 2:00 AM
./warp-manager-enhanced.py --schedule daily --schedule-time 02:00

# Weekly backup on Sundays at 3:00 AM
./warp-manager-enhanced.py --schedule weekly --schedule-time 03:00
```

### **Run Background Service**

```bash
# Start scheduler (runs in background)
./warp-manager-enhanced.py --start-scheduler

# Or use systemd service
systemctl --user start warp-backup-scheduler.service
systemctl --user enable warp-backup-scheduler.service
```

### **Check Service Status**

```bash
# View scheduler status
systemctl --user status warp-backup-scheduler.service

# View logs
journalctl --user -u warp-backup-scheduler.service -f
```

---

## 🖥️ **GUI Usage**

### **Launch GUI**

```bash
# Basic GUI
./warp-manager.py

# Enhanced GUI (coming soon)
# ./warp-manager-enhanced.py --gui
```

### **GUI Features**
- 📸 **One-click snapshot** button
- 💾 **Save Rules** and **Save MCP** buttons  
- 🗑️ **Delete database** with confirmation
- ⚠️ **Reset data** with safety backup
- 📝 **Sign up** - opens WARP registration
- 🌐 **Proxy settings** configuration
- 📋 **Backup browser** with restore options

---

## 📁 **File Locations**

### **Your Data**
```
Linux:
~/.config/warp-terminal/          # WARP configurations
~/.local/state/warp-terminal/     # Databases and MCP
~/.cache/warp-terminal/          # Cache files
~/.warp_profiles/                # User profiles

macOS:
~/Library/Application Support/warp-terminal/
~/Library/Caches/warp-terminal/

Windows:  
%APPDATA%/warp-terminal/
%LOCALAPPDATA%/warp-terminal/
```

### **Backups & Config**
```
~/.warp-backups/                 # All your backups
~/.warp-manager-config.json      # GitHub configuration
```

---

## 🔧 **Advanced Configuration**

### **Proxy Settings**

```bash
# Set proxy for GitHub operations
export HTTP_PROXY="http://proxy:8080"
export HTTPS_PROXY="http://proxy:8080"

# Or use GUI proxy settings
./warp-manager.py
# Click "Proxy Settings" button
```

### **Custom Backup Location**

```bash
# Override default backup directory
export WARP_BACKUP_DIR="/path/to/custom/backups"
```

### **Debug Mode**

```bash
# Enable debug output
export PYTHONDEBUG=1
./warp-manager-enhanced.py --list
```

---

## 📊 **Backup Format & Security**

### **Archive Format**
- **Compression**: Zstandard (fast, high ratio)
- **Naming**: `YYYY-MM-DDTHHMMSSZ-1.2.0-default-scope.tar.zst`
- **Integrity**: SHA256 verification for every file
- **Manifest**: JSON metadata with complete provenance

### **Example Backup Names**
```
2025-10-07T143022Z-1.2.0-default-rules.tar.zst
2025-10-07T143045Z-1.2.0-default-snapshot.tar.zst  
2025-10-07T143100Z-1.2.0-default-mcp-database.tar.zst
```

### **Security Features**
- 🛡️ **Pre-restore backups** - Always backup before restore
- ⚖️ **Safe reset mode** - Quarantine instead of deletion
- 🔍 **Integrity verification** - SHA256 checksums
- 🔐 **GitHub private repos** - Never public
- 🏠 **Local-first** - Works without internet

---

## 🌍 **Cross-Platform Support**

| OS | Status | Notes |
|----|--------|-------|
| **Linux** | ✅ Fully Supported | Debian, Ubuntu, Kali, Fedora, Arch |
| **macOS** | ✅ Supported | Intel & Apple Silicon |  
| **Windows** | ✅ Supported | Windows 10/11, WSL2 recommended |

### **Platform-Specific Setup**

**Linux (Debian/Ubuntu):**
```bash
sudo apt install python3 python3-pip python3-gi gir1.2-gtk-3.0
```

**macOS:**
```bash
brew install python-tk pygobject3
```

**Windows:**
```bash
# Use WSL2 or install Python + GTK
pip install pygobject
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

**❌ "No backups found"**
```bash
# Check backup directory exists
ls -la ~/.warp-backups/

# Try creating a test backup
./warp-manager.py --backup preferences
```

**❌ "GitHub upload failed"**
```bash
# Verify GitHub setup
./warp-manager-enhanced.py --list-remote

# Re-setup GitHub integration
./warp-manager-enhanced.py --setup-github
```

**❌ "GUI won't start"**
```bash
# Install GTK dependencies
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Use CLI instead
./warp-manager.py --help
```

**❌ "Permission denied"**
```bash
# Make scripts executable
chmod +x *.py

# Check Python installation
python3 --version
```

### **Get Help**

1. **Check logs**: `~/.local/state/warp-data-manager/logs/`
2. **GitHub Issues**: [Report a bug](https://github.com/EnkiJJK/warp-data-manager/issues)
3. **CLI Help**: `./warp-manager-enhanced.py --help`

---

## 🎯 **Use Cases & Scenarios**

### **👤 Individual Users**
- Daily WARP rule backups before experiments
- Safe system migrations with full restore
- Protecting valuable AI configurations

### **👥 Teams & Organizations**  
- Shared WARP configurations via GitHub
- Automated backup compliance
- Centralized configuration management

### **🔬 Researchers & Developers**
- Version control for AI experiment setups
- Reproducible research environments
- Safe testing of new WARP features

### **🏢 Enterprise**
- Scheduled backup policies
- Audit trail with GitHub integration
- Disaster recovery planning

---

## 🔄 **Migration & Data Transfer**

### **Move Between Machines**

**Export from old machine:**
```bash
./warp-manager-enhanced.py --snapshot --upload
```

**Import on new machine:**
```bash
git clone https://github.com/EnkiJJK/warp-data-manager.git
cd warp-data-manager
./warp-manager-enhanced.py --setup-github
./warp-manager-enhanced.py --list-remote
# Download and restore specific backup via GUI
```

### **Backup Before WARP Updates**

```bash
# Always backup before updates
./warp-manager-enhanced.py --snapshot
# Update WARP Terminal
# If issues occur, restore from backup
```

---

## 📈 **Project Status**

- ✅ **Stable Release**: v1.2.0 - Production Ready
- 🔄 **Active Development**: Regular updates
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/EnkiJJK/warp-data-manager/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/EnkiJJK/warp-data-manager/discussions)

### **Recent Updates**
- ✨ **v1.2.0**: GitHub sync, automated scheduling
- 🛡️ **v1.1.1**: Core backup functionality, GUI
- 🚀 **v1.0.0**: Initial release

---

## 🤝 **Contributing**

We welcome contributions! Here's how to help:

```bash
# Fork and clone
git clone https://github.com/YOUR-USERNAME/warp-data-manager.git
cd warp-data-manager

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
./deploy-fast.sh

# Submit pull request
```

### **Areas for Contribution**
- 🌍 Additional language support
- 🎨 UI/UX improvements
- 🔧 New backup formats
- 📱 Mobile companion apps
- 📚 Documentation improvements

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

**Free for personal and commercial use** ✨

---

## 🔗 **Links**

- **🌐 GitHub Repository**: https://github.com/EnkiJJK/warp-data-manager
- **📋 Issues**: https://github.com/EnkiJJK/warp-data-manager/issues
- **💬 Discussions**: https://github.com/EnkiJJK/warp-data-manager/discussions
- **📦 Releases**: https://github.com/EnkiJJK/warp-data-manager/releases

---

## 🎉 **Quick Start Checklist**

- [ ] Clone repository: `git clone https://github.com/EnkiJJK/warp-data-manager.git`
- [ ] Run quick deploy: `./deploy-fast.sh`  
- [ ] Create first backup: `./warp-manager-enhanced.py --snapshot`
- [ ] Setup GitHub (optional): `./warp-manager-enhanced.py --setup-github`
- [ ] Schedule automation (optional): `./warp-manager-enhanced.py --schedule daily`
- [ ] Bookmark this README for reference! 📖

---

**⚡ Fast • 🔒 Secure • 🎯 Reliable • 🌍 Cross-Platform**

*Built with ❤️ for the WARP Terminal community*
