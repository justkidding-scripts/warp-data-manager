# WARP Data Manager 🚀

Professional backup and management tool for WARP Terminal data with GUI and CLI interfaces.

## Features ⚡

- **📸 Take Snapshot** - One-click full backup of all WARP data
- **💾 Save Rules** - Backup only WARP rules and configurations  
- **🔧 Save MCP Servers** - Backup MCP server configurations
- **🗑️ Delete Database** - Clean local WARP database (with backup)
- **⚠️ Reset All Data** - Safe reset with quarantine backup
- **📝 Account Management** - Launch WARP signup page
- **🌐 Proxy Settings** - Configure proxy for network operations
- **🔄 Restore** - Restore from any backup with pre-restore safety backup
- **📋 List Backups** - View all available backups with metadata
- **✨ SemVer Naming** - Backups use semantic versioning (1.1.1 format)

## Installation 🛠️

```bash
git clone <this-repo>
cd warp-manager
chmod +x install.sh
./install.sh
```

## Usage 🎯

### GUI Mode (Default)
```bash
warp-manager
```

### CLI Mode
```bash
# Take complete snapshot
warp-manager --snapshot

# Save specific components
warp-manager --backup rules
warp-manager --backup mcp database
warp-manager --backup rules mcp preferences

# List backups
warp-manager --list

# Restore from backup
warp-manager --restore /home/user/.warp-backups/backup.tar.zst

# Reset WARP data (safe mode - moves to quarantine)
warp-manager --reset

# Delete local database only
warp-manager --delete-db

# Help
warp-manager --help
```

## Backup Types 📦

| Type | Description | Files |
|------|-------------|--------|
| `rules` | WARP AI rules and configurations | `*.md`, `*rule*`, `*warp*` files |
| `mcp` | MCP server configurations | `/mcp/` directory |
| `database` | WARP databases | `*.sqlite*` files |
| `preferences` | User preferences | `*.json` config files |  
| `logs` | Application logs | `*.log*` files |
| `profiles` | User profiles | `.warp_profiles/` |

## Backup Format 🗃️

- **Compression**: Zstandard (fast, high ratio)
- **Naming**: `YYYY-MM-DDTHHMMSSZ-1.1.1-default-scope.tar.zst`
- **Manifest**: JSON manifest with file hashes and metadata
- **Integrity**: SHA256 verification for each file

## Data Locations 📍

### Linux (Current OS)
- Config: `~/.config/warp-terminal/`
- State: `~/.local/state/warp-terminal/`
- Cache: `~/.cache/warp-terminal/`
- Profiles: `~/.warp_profiles/`
- Backups: `~/.warp-backups/`

### Cross-Platform Support
- macOS: `~/Library/Application Support/warp-terminal/`
- Windows: `%APPDATA%/warp-terminal/`

## Safety Features 🛡️

- **Pre-restore backup** - Automatic backup before any restore
- **Safe reset** - Moves data to quarantine instead of deletion
- **File integrity** - SHA256 verification of all files
- **Manifest tracking** - Complete metadata for each backup
- **Non-destructive** - All operations create backups first

## GUI Interface 🖥️

Clean, minimal interface with:
- Quick action buttons for common operations
- Backup browser with date/size information
- Progress indicators for long operations
- Confirmation dialogs for destructive operations
- Proxy configuration dialog
- Account management shortcuts

## Account Features 👤

- **Sign Up Button** - Opens Firefox to WARP signup page
- **Proxy Settings** - Configure HTTP/HTTPS proxies
- **Email Integration** - Store account email for quick access

## Network Safety 🌐

- App-scoped proxy settings only
- No system-wide network changes without confirmation
- Proxy test connectivity features
- Rollback instructions provided

## Advanced Features 🔧

- **Threaded operations** - Non-blocking GUI
- **Cross-platform paths** - Automatic OS detection  
- **Selective restore** - Choose specific components
- **Compression levels** - Optimized for speed vs. size
- **Manifest validation** - Verify backup integrity
- **Quarantine system** - Safe data recovery

## Development 🔨

```bash
# Run directly
python3 warp-manager.py

# CLI only
python3 warp-manager.py --cli --snapshot

# Debug mode
PYTHONDEBUG=1 python3 warp-manager.py
```

## Dependencies 📚

- Python 3.10+
- GTK 3.0 (for GUI)
- zstandard (compression)
- keyring (secure storage)

## License 📄

MIT License - See LICENSE file

---

**⚡ Fast • 🔒 Secure • 🎯 Reliable**

Professionally designed for cybersecurity researchers and WARP power users.