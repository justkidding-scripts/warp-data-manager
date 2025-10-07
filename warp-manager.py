#!/usr/bin/env python3
"""
WARP Data Manager - Backup, Restore & Manage WARP Terminal Data
Fast, professional tool for managing all WARP configurations and data.
"""
import os
import sys
import json
import shutil
import sqlite3
import tarfile
import zstandard as zstd
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import threading
import webbrowser
from dataclasses import dataclass, asdict

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib, Gdk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

@dataclass
class BackupManifest:
    """Backup manifest structure"""
    id: str
    timestamp: str
    semver: str
    os_type: str
    content_types: List[str]
    file_hashes: Dict[str, str]
    size: int
    encrypted: bool
    user: str
    machine: str

class WARPPaths:
    """Cross-platform WARP path detection"""
    
    @staticmethod
    def get_home() -> Path:
        return Path.home()
    
    @staticmethod
    def get_warp_paths() -> Dict[str, Path]:
        """Get all WARP data paths for current OS"""
        home = WARPPaths.get_home()
        
        if sys.platform == "linux":
            return {
                "config": home / ".config" / "warp-terminal",
                "state": home / ".local" / "state" / "warp-terminal", 
                "cache": home / ".cache" / "warp-terminal",
                "profiles": home / ".warp_profiles",
                "cloudflare": home / ".local" / "share" / "cloudflare-warp-gui"
            }
        elif sys.platform == "darwin":
            return {
                "config": home / "Library" / "Application Support" / "warp-terminal",
                "state": home / "Library" / "Application Support" / "warp-terminal" / "state",
                "cache": home / "Library" / "Caches" / "warp-terminal",
                "profiles": home / ".warp_profiles"
            }
        elif sys.platform.startswith("win"):
            appdata = Path(os.getenv("APPDATA", home / "AppData" / "Roaming"))
            localappdata = Path(os.getenv("LOCALAPPDATA", home / "AppData" / "Local"))
            return {
                "config": appdata / "warp-terminal",
                "state": localappdata / "warp-terminal",
                "cache": localappdata / "warp-terminal" / "cache",
                "profiles": home / ".warp_profiles"
            }
        else:
            return {}

class WARPManager:
    """Core WARP data management engine"""
    
    def __init__(self):
        self.home = Path.home()
        self.backup_dir = self.home / ".warp-backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.paths = WARPPaths.get_warp_paths()
        self.current_version = "1.1.1"
        
    def get_existing_paths(self) -> Dict[str, Path]:
        """Return only paths that actually exist"""
        return {k: v for k, v in self.paths.items() if v.exists()}
    
    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error hashing {filepath}: {e}")
            return ""
    
    def create_manifest(self, content_types: List[str], file_hashes: Dict[str, str], size: int) -> BackupManifest:
        """Create backup manifest"""
        return BackupManifest(
            id=datetime.now().strftime("%Y%m%d%H%M%S"),
            timestamp=datetime.now().isoformat(),
            semver=self.current_version,
            os_type=sys.platform,
            content_types=content_types,
            file_hashes=file_hashes,
            size=size,
            encrypted=False,
            user=os.getenv("USER", "unknown"),
            machine=os.getenv("HOSTNAME", "unknown")
        )
    
    def backup_selective(self, types: List[str]) -> Optional[Path]:
        """Create selective backup of specific types"""
        timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%SZ")
        scope = "-".join(types) if types else "full"
        backup_name = f"{timestamp}-{self.current_version}-default-{scope}.tar.zst"
        backup_path = self.backup_dir / backup_name
        
        print(f"Creating backup: {backup_name}")
        
        # Collect files based on types
        files_to_backup = []
        file_hashes = {}
        
        existing_paths = self.get_existing_paths()
        
        for backup_type in types:
            if backup_type == "rules":
                config_path = existing_paths.get("config")
                if config_path:
                    for rule_file in config_path.glob("*.md"):
                        if "rule" in rule_file.name.lower() or "warp" in rule_file.name.lower():
                            files_to_backup.append(rule_file)
                            
            elif backup_type == "mcp":
                state_path = existing_paths.get("state")
                if state_path:
                    mcp_path = state_path / "mcp"
                    if mcp_path.exists():
                        for mcp_file in mcp_path.rglob("*"):
                            if mcp_file.is_file():
                                files_to_backup.append(mcp_file)
                                
            elif backup_type == "database":
                state_path = existing_paths.get("state")
                if state_path:
                    for db_file in state_path.glob("*.sqlite*"):
                        files_to_backup.append(db_file)
                        
            elif backup_type == "preferences":
                config_path = existing_paths.get("config")
                if config_path:
                    for pref_file in config_path.glob("*.json"):
                        files_to_backup.append(pref_file)
                        
            elif backup_type == "logs":
                state_path = existing_paths.get("state")
                if state_path:
                    for log_file in state_path.glob("*.log*"):
                        files_to_backup.append(log_file)
                        
            elif backup_type == "profiles":
                profiles_path = existing_paths.get("profiles")
                if profiles_path and profiles_path.exists():
                    for profile_file in profiles_path.rglob("*"):
                        if profile_file.is_file():
                            files_to_backup.append(profile_file)
        
        # Remove duplicates
        files_to_backup = list(set(files_to_backup))
        
        if not files_to_backup:
            print("No files found to backup")
            return None
            
        # Calculate hashes
        for file_path in files_to_backup:
            file_hashes[str(file_path)] = self.calculate_file_hash(file_path)
        
        # Create compressed archive
        try:
            with open(backup_path, 'wb') as f:
                cctx = zstd.ZstdCompressor(level=3, threads=-1)
                with cctx.stream_writer(f) as compressor:
                    with tarfile.open(fileobj=compressor, mode='w|') as tar:
                        for file_path in files_to_backup:
                            try:
                                # Use relative path from home
                                arcname = str(file_path.relative_to(self.home))
                                tar.add(str(file_path), arcname=arcname)
                            except Exception as e:
                                print(f"Error adding {file_path}: {e}")
                                continue
                        
                        # Add manifest
                        manifest = self.create_manifest(types, file_hashes, 0)
                        manifest_json = json.dumps(asdict(manifest), indent=2)
                        
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_manifest:
                            temp_manifest.write(manifest_json)
                            temp_manifest.flush()
                            tar.add(temp_manifest.name, arcname="manifest.json")
                        os.unlink(temp_manifest.name)
            
            # Save external manifest
            manifest_path = backup_path.with_suffix('.manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(asdict(manifest), f, indent=2)
                
            print(f"Backup created: {backup_path}")
            print(f"Files backed up: {len(files_to_backup)}")
            return backup_path
            
        except Exception as e:
            print(f"Backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def take_snapshot(self) -> Optional[Path]:
        """Take complete snapshot of all WARP data"""
        return self.backup_selective(["rules", "mcp", "database", "preferences", "logs", "profiles"])
    
    def list_backups(self) -> List[Path]:
        """List all available backups"""
        if not self.backup_dir.exists():
            return []
        return sorted([f for f in self.backup_dir.iterdir() if f.suffix == '.zst'])
    
    def restore_backup(self, backup_path: Path, dry_run: bool = False) -> bool:
        """Restore from backup"""
        if not backup_path.exists():
            print(f"Backup not found: {backup_path}")
            return False
        
        if dry_run:
            print(f"DRY RUN: Would restore from {backup_path}")
            return True
        
        # Create pre-restore backup
        print("Creating pre-restore backup...")
        pre_restore = self.take_snapshot()
        if pre_restore:
            print(f"Pre-restore backup: {pre_restore}")
        
        try:
            print(f"Restoring from: {backup_path}")
            
            # Extract archive
            with open(backup_path, 'rb') as f:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(f) as decompressor:
                    with tarfile.open(fileobj=decompressor, mode='r|') as tar:
                        tar.extractall(path=self.home)
            
            print("Restore completed successfully")
            return True
            
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    def reset_warp_data(self, safe_mode: bool = True) -> bool:
        """Reset WARP data (safe or destructive)"""
        if safe_mode:
            # Create backup first
            backup = self.take_snapshot()
            if backup:
                print(f"Backup created before reset: {backup}")
            
            # Move to quarantine
            quarantine_dir = self.backup_dir / f"quarantine-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            quarantine_dir.mkdir(exist_ok=True)
            
            for name, path in self.get_existing_paths().items():
                if path.exists():
                    dest = quarantine_dir / name
                    shutil.move(str(path), str(dest))
                    print(f"Moved {path} to quarantine")
            
            print(f"WARP data moved to quarantine: {quarantine_dir}")
            return True
        else:
            # Destructive wipe
            for name, path in self.get_existing_paths().items():
                if path.exists():
                    shutil.rmtree(str(path))
                    print(f"Deleted: {path}")
            
            print("WARP data destructively wiped")
            return True
    
    def delete_local_database(self) -> bool:
        """Delete local WARP database"""
        state_path = self.paths.get("state")
        if not state_path or not state_path.exists():
            print("No WARP state directory found")
            return False
        
        # Create backup first
        backup = self.backup_selective(["database"])
        if backup:
            print(f"Database backup created: {backup}")
        
        # Delete database files
        db_files = list(state_path.glob("*.sqlite*"))
        for db_file in db_files:
            try:
                db_file.unlink()
                print(f"Deleted: {db_file}")
            except Exception as e:
                print(f"Error deleting {db_file}: {e}")
        
        return len(db_files) > 0

class WARPManagerGUI:
    """GTK GUI for WARP Manager"""
    
    def __init__(self):
        self.manager = WARPManager()
        self.window = None
        self.progress_bar = None
        
    def create_gui(self):
        """Create the main GUI"""
        self.window = Gtk.Window()
        self.window.set_title("WARP Data Manager")
        self.window.set_default_size(600, 500)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Main container
        vbox = Gtk.VBox(spacing=10)
        vbox.set_margin_left(20)
        vbox.set_margin_right(20)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<big><b>WARP Data Manager</b></big>")
        vbox.pack_start(title, False, False, 0)
        
        # Quick Actions Frame
        actions_frame = Gtk.Frame(label="Quick Actions")
        actions_box = Gtk.VBox(spacing=5)
        actions_box.set_margin_left(10)
        actions_box.set_margin_right(10)
        actions_box.set_margin_top(10)
        actions_box.set_margin_bottom(10)
        
        # Snapshot button
        snapshot_btn = Gtk.Button(label="📸 Take Snapshot")
        snapshot_btn.connect("clicked", self.on_snapshot_clicked)
        actions_box.pack_start(snapshot_btn, False, False, 0)
        
        # Selective backup buttons
        rules_btn = Gtk.Button(label="💾 Save Rules")
        rules_btn.connect("clicked", lambda w: self.on_selective_backup(["rules"]))
        actions_box.pack_start(rules_btn, False, False, 0)
        
        mcp_btn = Gtk.Button(label="🔧 Save MCP Servers")
        mcp_btn.connect("clicked", lambda w: self.on_selective_backup(["mcp"]))
        actions_box.pack_start(mcp_btn, False, False, 0)
        
        actions_frame.add(actions_box)
        vbox.pack_start(actions_frame, False, False, 0)
        
        # Data Management Frame
        data_frame = Gtk.Frame(label="Data Management")
        data_box = Gtk.VBox(spacing=5)
        data_box.set_margin_left(10)
        data_box.set_margin_right(10)
        data_box.set_margin_top(10)
        data_box.set_margin_bottom(10)
        
        # Delete database button
        delete_db_btn = Gtk.Button(label="🗑️ Delete My Data from WARP Database")
        delete_db_btn.connect("clicked", self.on_delete_database_clicked)
        delete_db_btn.get_style_context().add_class("destructive-action")
        data_box.pack_start(delete_db_btn, False, False, 0)
        
        # Reset button
        reset_btn = Gtk.Button(label="⚠️ Reset All WARP Data")
        reset_btn.connect("clicked", self.on_reset_clicked)
        reset_btn.get_style_context().add_class("destructive-action")
        data_box.pack_start(reset_btn, False, False, 0)
        
        data_frame.add(data_box)
        vbox.pack_start(data_frame, False, False, 0)
        
        # Account Management Frame
        account_frame = Gtk.Frame(label="Account Management")
        account_box = Gtk.VBox(spacing=5)
        account_box.set_margin_left(10)
        account_box.set_margin_right(10)
        account_box.set_margin_top(10)
        account_box.set_margin_bottom(10)
        
        # Sign up button
        signup_btn = Gtk.Button(label="📝 Sign Up for WARP")
        signup_btn.connect("clicked", self.on_signup_clicked)
        account_box.pack_start(signup_btn, False, False, 0)
        
        # Proxy settings button
        proxy_btn = Gtk.Button(label="🌐 Proxy Settings")
        proxy_btn.connect("clicked", self.on_proxy_settings_clicked)
        account_box.pack_start(proxy_btn, False, False, 0)
        
        account_frame.add(account_box)
        vbox.pack_start(account_frame, False, False, 0)
        
        # Backups Frame
        backups_frame = Gtk.Frame(label="Available Backups")
        backups_box = Gtk.VBox(spacing=5)
        backups_box.set_margin_left(10)
        backups_box.set_margin_right(10)
        backups_box.set_margin_top(10)
        backups_box.set_margin_bottom(10)
        
        # Backups list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(150)
        
        self.backups_store = Gtk.ListStore(str, str, str)  # name, date, size
        self.backups_view = Gtk.TreeView(model=self.backups_store)
        
        name_col = Gtk.TreeViewColumn("Backup Name", Gtk.CellRendererText(), text=0)
        date_col = Gtk.TreeViewColumn("Date", Gtk.CellRendererText(), text=1)
        size_col = Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=2)
        
        self.backups_view.append_column(name_col)
        self.backups_view.append_column(date_col)
        self.backups_view.append_column(size_col)
        
        scroll.add(self.backups_view)
        backups_box.pack_start(scroll, True, True, 0)
        
        # Restore button
        restore_btn = Gtk.Button(label="🔄 Restore Selected")
        restore_btn.connect("clicked", self.on_restore_clicked)
        backups_box.pack_start(restore_btn, False, False, 0)
        
        backups_frame.add(backups_box)
        vbox.pack_start(backups_frame, True, True, 0)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_text("Ready")
        self.progress_bar.set_show_text(True)
        vbox.pack_start(self.progress_bar, False, False, 0)
        
        self.window.add(vbox)
        self.refresh_backups_list()
        
    def run_in_thread(self, func, *args, **kwargs):
        """Run function in thread with progress feedback"""
        def worker():
            try:
                GLib.idle_add(self.progress_bar.pulse)
                result = func(*args, **kwargs)
                GLib.idle_add(self.on_operation_complete, f"{func.__name__} completed")
                GLib.idle_add(self.refresh_backups_list)
            except Exception as e:
                GLib.idle_add(self.on_operation_complete, f"Error: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def on_operation_complete(self, message):
        """Handle operation completion"""
        self.progress_bar.set_fraction(0)
        self.progress_bar.set_text(message)
        
    def on_snapshot_clicked(self, widget):
        """Handle snapshot button click"""
        self.progress_bar.set_text("Taking snapshot...")
        self.run_in_thread(self.manager.take_snapshot)
    
    def on_selective_backup(self, types):
        """Handle selective backup"""
        self.progress_bar.set_text(f"Backing up {', '.join(types)}...")
        self.run_in_thread(self.manager.backup_selective, types)
    
    def on_delete_database_clicked(self, widget):
        """Handle delete database button"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete WARP Database?"
        )
        dialog.format_secondary_text(
            "This will delete your local WARP database. A backup will be created first. Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.progress_bar.set_text("Deleting database...")
            self.run_in_thread(self.manager.delete_local_database)
    
    def on_reset_clicked(self, widget):
        """Handle reset button"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Reset All WARP Data?"
        )
        dialog.format_secondary_text(
            "This will reset all WARP data (safe mode - moved to quarantine). A backup will be created first. Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.progress_bar.set_text("Resetting WARP data...")
            self.run_in_thread(self.manager.reset_warp_data, True)
    
    def on_signup_clicked(self, widget):
        """Handle sign up button"""
        try:
            webbrowser.open("https://app.warp.dev/signup")
            self.progress_bar.set_text("Opened WARP signup page")
        except Exception as e:
            self.progress_bar.set_text(f"Error opening browser: {e}")
    
    def on_proxy_settings_clicked(self, widget):
        """Handle proxy settings button"""
        self.show_proxy_dialog()
    
    def show_proxy_dialog(self):
        """Show proxy configuration dialog"""
        dialog = Gtk.Dialog(title="Proxy Settings", transient_for=self.window, flags=0)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content = dialog.get_content_area()
        
        # HTTP Proxy
        http_box = Gtk.HBox(spacing=10)
        http_label = Gtk.Label("HTTP Proxy:")
        http_label.set_size_request(100, -1)
        http_entry = Gtk.Entry()
        http_entry.set_text(os.getenv("HTTP_PROXY", ""))
        http_box.pack_start(http_label, False, False, 0)
        http_box.pack_start(http_entry, True, True, 0)
        content.pack_start(http_box, False, False, 5)
        
        # HTTPS Proxy
        https_box = Gtk.HBox(spacing=10)
        https_label = Gtk.Label("HTTPS Proxy:")
        https_label.set_size_request(100, -1)
        https_entry = Gtk.Entry()
        https_entry.set_text(os.getenv("HTTPS_PROXY", ""))
        https_box.pack_start(https_label, False, False, 0)
        https_box.pack_start(https_entry, True, True, 0)
        content.pack_start(https_box, False, False, 5)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Set environment variables for this session
            os.environ["HTTP_PROXY"] = http_entry.get_text()
            os.environ["HTTPS_PROXY"] = https_entry.get_text()
            self.progress_bar.set_text("Proxy settings updated")
        
        dialog.destroy()
    
    def on_restore_clicked(self, widget):
        """Handle restore button"""
        selection = self.backups_view.get_selection()
        model, treeiter = selection.get_selected()
        
        if treeiter:
            backup_name = model[treeiter][0]
            backup_path = self.manager.backup_dir / backup_name
            
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Restore from {backup_name}?"
            )
            dialog.format_secondary_text(
                "This will restore the selected backup. A pre-restore backup will be created. Continue?"
            )
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                self.progress_bar.set_text("Restoring backup...")
                self.run_in_thread(self.manager.restore_backup, backup_path)
    
    def refresh_backups_list(self):
        """Refresh the backups list"""
        self.backups_store.clear()
        
        for backup in self.manager.list_backups():
            try:
                stat = backup.stat()
                size = f"{stat.st_size // 1024} KB"
                date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                self.backups_store.append([backup.name, date, size])
            except Exception as e:
                print(f"Error reading backup {backup}: {e}")
    
    def run(self):
        """Run the GUI"""
        self.create_gui()
        self.window.show_all()
        Gtk.main()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WARP Data Manager")
    parser.add_argument("--cli", action="store_true", help="Use CLI mode")
    parser.add_argument("--snapshot", action="store_true", help="Take snapshot")
    parser.add_argument("--backup", nargs="+", choices=["rules", "mcp", "database", "preferences", "logs", "profiles"], help="Selective backup")
    parser.add_argument("--restore", type=str, help="Restore from backup file")
    parser.add_argument("--reset", action="store_true", help="Reset WARP data (safe mode)")
    parser.add_argument("--delete-db", action="store_true", help="Delete local database")
    parser.add_argument("--list", action="store_true", help="List backups")
    
    args = parser.parse_args()
    
    manager = WARPManager()
    
    if args.cli or any([args.snapshot, args.backup, args.restore, args.reset, args.delete_db, args.list]):
        # CLI Mode
        if args.snapshot:
            result = manager.take_snapshot()
            print(f"Snapshot: {result}")
            
        elif args.backup:
            result = manager.backup_selective(args.backup)
            print(f"Backup: {result}")
            
        elif args.restore:
            backup_path = Path(args.restore)
            result = manager.restore_backup(backup_path)
            print(f"Restore: {'Success' if result else 'Failed'}")
            
        elif args.reset:
            result = manager.reset_warp_data()
            print(f"Reset: {'Success' if result else 'Failed'}")
            
        elif args.delete_db:
            result = manager.delete_local_database()
            print(f"Delete DB: {'Success' if result else 'Failed'}")
            
        elif args.list:
            backups = manager.list_backups()
            if backups:
                print("Available backups:")
                for backup in backups:
                    stat = backup.stat()
                    size = f"{stat.st_size // 1024} KB"
                    date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    print(f"  {backup.name} - {date} - {size}")
            else:
                print("No backups found")
    else:
        # GUI Mode
        if not GUI_AVAILABLE:
            print("GUI not available. Install GTK3 and PyGObject.")
            print("Using CLI mode instead.")
            print("Usage: ./warp-manager.py --help")
            return
        
        gui = WARPManagerGUI()
        gui.run()

if __name__ == "__main__":
    main()