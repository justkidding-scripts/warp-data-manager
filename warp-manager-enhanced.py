#!/usr/bin/env python3
"""
WARP Data Manager Enhanced - GitHub Integration + Scheduler
Professional WARP Terminal data backup with remote sync and automation.
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
import requests
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
import threading
import webbrowser
from dataclasses import dataclass, asdict
import time
import schedule

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
    """Enhanced backup manifest with GitHub metadata"""
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
    github_url: Optional[str] = None
    github_sha: Optional[str] = None

class GitHubSync:
    """GitHub repository backup sync"""
    
    def __init__(self):
        self.token = None
        self.repo_owner = None
        self.repo_name = None
        self.load_config()
    
    def load_config(self):
        """Load GitHub configuration"""
        config_file = Path.home() / ".warp-manager-config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    self.token = config.get("github_token")
                    self.repo_owner = config.get("github_owner")
                    self.repo_name = config.get("github_repo", "warp-backups")
            except Exception as e:
                print(f"Config load error: {e}")
    
    def save_config(self, token: str, owner: str, repo: str = "warp-backups"):
        """Save GitHub configuration"""
        config_file = Path.home() / ".warp-manager-config.json"
        config = {
            "github_token": token,
            "github_owner": owner,
            "github_repo": repo
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Store token in keyring if available
        if KEYRING_AVAILABLE:
            keyring.set_password("warp-manager", "github_token", token)
        
        self.token = token
        self.repo_owner = owner
        self.repo_name = repo
    
    def test_connection(self) -> bool:
        """Test GitHub API connection"""
        if not self.token or not self.repo_owner:
            return False
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def create_repo_if_needed(self) -> bool:
        """Create private backup repo if it doesn't exist"""
        if not self.token:
            return False
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Check if repo exists
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return True
        except Exception:
            pass
        
        # Create repo
        try:
            data = {
                "name": self.repo_name,
                "private": True,
                "description": "Private WARP Terminal backup repository",
                "auto_init": True
            }
            response = requests.post(
                "https://api.github.com/user/repos",
                headers=headers,
                json=data,
                timeout=30
            )
            return response.status_code == 201
        except Exception:
            return False
    
    def upload_backup(self, backup_path: Path) -> Optional[Dict]:
        """Upload backup to GitHub"""
        if not self.test_connection():
            return None
        
        try:
            # Read backup file
            with open(backup_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode()
            
            # Upload to GitHub
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "message": f"Backup: {backup_path.name}",
                "content": content,
                "branch": "main"
            }
            
            response = requests.put(
                f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/backups/{backup_path.name}",
                headers=headers,
                json=data,
                timeout=300  # 5 minute timeout for large files
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"GitHub upload failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Upload error: {e}")
            return None
    
    def list_remote_backups(self) -> List[Dict]:
        """List backups in GitHub repo"""
        if not self.test_connection():
            return []
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/backups",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []
    
    def download_backup(self, filename: str, local_path: Path) -> bool:
        """Download backup from GitHub"""
        if not self.test_connection():
            return False
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/backups/{filename}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data['content'])
                
                with open(local_path, 'wb') as f:
                    f.write(content)
                return True
            return False
        except Exception:
            return False

class WARPScheduler:
    """Automated backup scheduler"""
    
    def __init__(self, manager):
        self.manager = manager
        self.github = GitHubSync()
        self.running = False
        self.thread = None
    
    def schedule_daily_backup(self, time_str: str = "02:00"):
        """Schedule daily backup at specified time"""
        schedule.clear()
        schedule.every().day.at(time_str).do(self.run_scheduled_backup)
        print(f"Scheduled daily backup at {time_str}")
    
    def schedule_weekly_backup(self, day: str = "sunday", time_str: str = "03:00"):
        """Schedule weekly backup"""
        schedule.clear()
        getattr(schedule.every(), day.lower()).at(time_str).do(self.run_scheduled_snapshot)
        print(f"Scheduled weekly snapshot on {day} at {time_str}")
    
    def run_scheduled_backup(self):
        """Execute scheduled backup"""
        print("Running scheduled backup...")
        backup_path = self.manager.backup_selective(["rules", "mcp", "preferences"])
        
        if backup_path and self.github.test_connection():
            print("Uploading to GitHub...")
            result = self.github.upload_backup(backup_path)
            if result:
                print("Backup uploaded to GitHub successfully")
            else:
                print("GitHub upload failed")
    
    def run_scheduled_snapshot(self):
        """Execute scheduled full snapshot"""
        print("Running scheduled snapshot...")
        backup_path = self.manager.take_snapshot()
        
        if backup_path and self.github.test_connection():
            print("Uploading snapshot to GitHub...")
            result = self.github.upload_backup(backup_path)
            if result:
                print("Snapshot uploaded to GitHub successfully")
    
    def start_scheduler(self):
        """Start the scheduler thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        print("Scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

class WARPManagerEnhanced:
    """Enhanced WARP Manager with GitHub sync and scheduling"""
    
    def __init__(self):
        self.home = Path.home()
        self.backup_dir = self.home / ".warp-backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.paths = self._get_warp_paths()
        self.current_version = "1.2.0"  # Enhanced version
        self.github = GitHubSync()
        self.scheduler = WARPScheduler(self)
    
    def _get_warp_paths(self) -> Dict[str, Path]:
        """Get WARP paths for current OS"""
        home = self.home
        
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
    
    def backup_with_sync(self, types: List[str], upload_to_github: bool = False) -> Optional[Path]:
        """Create backup and optionally sync to GitHub"""
        backup_path = self.backup_selective(types)
        
        if backup_path and upload_to_github and self.github.test_connection():
            print("Uploading to GitHub...")
            result = self.github.upload_backup(backup_path)
            if result:
                print("✅ Backup uploaded to GitHub successfully")
                return backup_path
            else:
                print("❌ GitHub upload failed")
        
        return backup_path
    
    def backup_selective(self, types: List[str]) -> Optional[Path]:
        """Create selective backup (same as base class but with enhanced manifest)"""
        timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%SZ")
        scope = "-".join(types) if types else "full"
        backup_name = f"{timestamp}-{self.current_version}-default-{scope}.tar.zst"
        backup_path = self.backup_dir / backup_name
        
        print(f"Creating backup: {backup_name}")
        
        files_to_backup = []
        file_hashes = {}
        
        existing_paths = {k: v for k, v in self.paths.items() if v.exists()}
        
        # Collect files based on types (same logic as base class)
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
        
        files_to_backup = list(set(files_to_backup))
        
        if not files_to_backup:
            print("No files found to backup")
            return None
        
        # Calculate hashes
        for file_path in files_to_backup:
            file_hashes[str(file_path)] = self.calculate_file_hash(file_path)
        
        # Create archive
        try:
            with open(backup_path, 'wb') as f:
                cctx = zstd.ZstdCompressor(level=3, threads=-1)
                with cctx.stream_writer(f) as compressor:
                    with tarfile.open(fileobj=compressor, mode='w|') as tar:
                        for file_path in files_to_backup:
                            try:
                                arcname = str(file_path.relative_to(self.home))
                                tar.add(str(file_path), arcname=arcname)
                            except Exception as e:
                                print(f"Error adding {file_path}: {e}")
                                continue
                        
                        # Add enhanced manifest
                        manifest = BackupManifest(
                            id=datetime.now().strftime("%Y%m%d%H%M%S"),
                            timestamp=datetime.now().isoformat(),
                            semver=self.current_version,
                            os_type=sys.platform,
                            content_types=types,
                            file_hashes=file_hashes,
                            size=len(files_to_backup),
                            encrypted=False,
                            user=os.getenv("USER", "unknown"),
                            machine=os.getenv("HOSTNAME", "unknown")
                        )
                        
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
            
            print(f"✅ Backup created: {backup_path}")
            print(f"📁 Files backed up: {len(files_to_backup)}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error hashing {filepath}: {e}")
            return ""
    
    def take_snapshot(self) -> Optional[Path]:
        """Take complete snapshot"""
        return self.backup_selective(["rules", "mcp", "database", "preferences", "logs", "profiles"])
    
    def sync_all_to_github(self) -> int:
        """Sync all local backups to GitHub"""
        if not self.github.test_connection():
            print("❌ GitHub not configured or unreachable")
            return 0
        
        backups = self.list_backups()
        uploaded = 0
        
        for backup_path in backups:
            print(f"Uploading {backup_path.name}...")
            result = self.github.upload_backup(backup_path)
            if result:
                uploaded += 1
                print(f"✅ Uploaded {backup_path.name}")
            else:
                print(f"❌ Failed to upload {backup_path.name}")
        
        return uploaded
    
    def list_backups(self) -> List[Path]:
        """List local backups"""
        if not self.backup_dir.exists():
            return []
        return sorted([f for f in self.backup_dir.iterdir() if f.suffix == '.zst'])

def main():
    """Enhanced main function with GitHub and scheduler options"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WARP Data Manager Enhanced")
    parser.add_argument("--cli", action="store_true", help="Use CLI mode")
    parser.add_argument("--snapshot", action="store_true", help="Take snapshot")
    parser.add_argument("--backup", nargs="+", choices=["rules", "mcp", "database", "preferences", "logs", "profiles"], help="Selective backup")
    parser.add_argument("--upload", action="store_true", help="Upload backup to GitHub")
    parser.add_argument("--sync-all", action="store_true", help="Sync all backups to GitHub")
    parser.add_argument("--setup-github", action="store_true", help="Setup GitHub integration")
    parser.add_argument("--schedule", choices=["daily", "weekly"], help="Setup scheduled backups")
    parser.add_argument("--schedule-time", default="02:00", help="Schedule time (HH:MM)")
    parser.add_argument("--start-scheduler", action="store_true", help="Start scheduler daemon")
    parser.add_argument("--list", action="store_true", help="List backups")
    parser.add_argument("--list-remote", action="store_true", help="List remote backups")
    
    args = parser.parse_args()
    
    manager = WARPManagerEnhanced()
    
    if args.setup_github:
        print("🔧 GitHub Setup")
        token = input("GitHub Personal Access Token: ").strip()
        owner = input("GitHub Username/Organization: ").strip()
        repo = input("Repository Name [warp-backups]: ").strip() or "warp-backups"
        
        manager.github.save_config(token, owner, repo)
        
        if manager.github.create_repo_if_needed():
            print("✅ GitHub repository configured successfully")
        else:
            print("❌ Failed to create/access repository")
        return
    
    if args.sync_all:
        uploaded = manager.sync_all_to_github()
        print(f"✅ Uploaded {uploaded} backups to GitHub")
        return
    
    if args.list_remote:
        remotes = manager.github.list_remote_backups()
        if remotes:
            print("Remote backups:")
            for backup in remotes:
                print(f"  📁 {backup['name']}")
        else:
            print("No remote backups found")
        return
    
    if args.schedule:
        if args.schedule == "daily":
            manager.scheduler.schedule_daily_backup(args.schedule_time)
        elif args.schedule == "weekly":
            manager.scheduler.schedule_weekly_backup("sunday", args.schedule_time)
        print(f"✅ Scheduled {args.schedule} backups")
        return
    
    if args.start_scheduler:
        print("🕐 Starting backup scheduler...")
        manager.scheduler.start_scheduler()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            manager.scheduler.stop_scheduler()
            print("Scheduler stopped")
        return
    
    # Handle regular backup commands
    if args.cli or any([args.snapshot, args.backup, args.list]):
        if args.snapshot:
            backup_path = manager.backup_with_sync(
                ["rules", "mcp", "database", "preferences", "logs", "profiles"],
                args.upload
            )
            print(f"Snapshot: {backup_path}")
            
        elif args.backup:
            backup_path = manager.backup_with_sync(args.backup, args.upload)
            print(f"Backup: {backup_path}")
            
        elif args.list:
            backups = manager.list_backups()
            if backups:
                print("Local backups:")
                for backup in backups:
                    stat = backup.stat()
                    size = f"{stat.st_size // 1024} KB"
                    date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    print(f"  📁 {backup.name} - {date} - {size}")
            else:
                print("No backups found")
    else:
        print("WARP Data Manager Enhanced v1.2.0")
        print("Usage: ./warp-manager-enhanced.py --help")
        print("Setup: ./warp-manager-enhanced.py --setup-github")

if __name__ == "__main__":
    main()