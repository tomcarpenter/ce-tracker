"""
Sync module - File synchronization between primary and backup locations.
Watches for changes and mirrors certificates to backup destinations.
"""

from pathlib import Path
from typing import Optional, Callable
import shutil


class FileSync:
    """Manage file synchronization between locations."""
    
    def __init__(self, primary_dir: Path, backup_dir: Optional[Path] = None):
        self.primary_dir = Path(primary_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else None
        
        self.primary_dir.mkdir(parents=True, exist_ok=True)
        if self.backup_dir:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def sync_to_backup(self, file_path: Path) -> bool:
        """Copy a file from primary to backup location."""
        if not self.backup_dir:
            return True  # No backup configured
        
        try:
            relative_path = file_path.relative_to(self.primary_dir)
            backup_path = self.backup_dir / relative_path
            
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            
            return True
        except Exception:
            return False
    
    def sync_from_backup(self, file_path: Path) -> bool:
        """Restore a file from backup to primary location."""
        if not self.backup_dir:
            return False
        
        try:
            relative_path = file_path.relative_to(self.primary_dir)
            backup_path = self.backup_dir / relative_path
            
            if not backup_path.exists():
                return False
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, file_path)
            
            return True
        except Exception:
            return False
    
    def list_synced_files(self) -> list[Path]:
        """List all files in primary directory."""
        return list(self.primary_dir.rglob("*")) if self.primary_dir.exists() else []
    
    def verify_backup_exists(self, file_path: Path) -> bool:
        """Check if file has backup copy."""
        if not self.backup_dir:
            return False
        
        try:
            relative_path = file_path.relative_to(self.primary_dir)
            backup_path = self.backup_dir / relative_path
            return backup_path.exists()
        except Exception:
            return False
