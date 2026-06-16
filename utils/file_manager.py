"""
File Manager module - Certificate storage and management.
Handles UUID naming, metadata, and dual-location storage.
"""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json
import shutil


class CertificateManager:
    """Manage certificate storage with UUID naming and metadata."""
    
    def __init__(self, root_dir: Path,
                 backup_dir: Optional[Path] = None,
                 backup_metadata_dir: Optional[Path] = None):
        self.root_dir = Path(root_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else None
        self.metadata_dir = self.root_dir.parent / "metadata"
        self.backup_metadata_dir = Path(backup_metadata_dir) if backup_metadata_dir else (
            self.backup_dir.parent / "metadata" if self.backup_dir else None
        )
        
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        if self.backup_dir:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        if self.backup_metadata_dir:
            self.backup_metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def store_certificate(self, file_data: bytes, original_filename: str, 
                         file_hash: str, record_id: str) -> Optional[str]:
        """
        Store certificate with UUID naming and metadata.
        Returns UUID filename on success.
        """
        try:
            # Generate UUID filename, preserve extension
            file_ext = Path(original_filename).suffix
            cert_uuid = str(uuid.uuid4())
            cert_filename = f"{cert_uuid}{file_ext}"
            
            # Write to root directory
            cert_path = self.root_dir / cert_filename
            with open(cert_path, "wb") as f:
                f.write(file_data)
            
            # Write to backup if configured
            if self.backup_dir:
                backup_path = self.backup_dir / cert_filename
                with open(backup_path, "wb") as f:
                    f.write(file_data)
            
            # Store metadata
            metadata = {
                "uuid": cert_uuid,
                "original_filename": original_filename,
                "stored_filename": cert_filename,
                "file_hash": file_hash,
                "record_id": record_id,
                "stored_at": datetime.now().isoformat(),
            }
            
            metadata_path = self.metadata_dir / f"{cert_uuid}.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            if self.backup_metadata_dir:
                backup_metadata_path = self.backup_metadata_dir / f"{cert_uuid}.json"
                with open(backup_metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
            
            return cert_uuid
        
        except Exception as e:
            print(f"Error storing certificate: {e}")
            return None
    
    def retrieve_certificate(self, cert_uuid: str) -> Optional[bytes]:
        """Retrieve certificate by UUID."""
        try:
            # Try root directory first
            metadata_path = self.metadata_dir / f"{cert_uuid}.json"
            
            if not metadata_path.exists():
                if not self.backup_metadata_dir:
                    return None
                metadata_path = self.backup_metadata_dir / f"{cert_uuid}.json"
                if not metadata_path.exists():
                    return None
            
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            cert_filename = metadata["stored_filename"]
            cert_path = self.root_dir / cert_filename
            
            if cert_path.exists():
                with open(cert_path, "rb") as f:
                    return f.read()
            
            # Try backup if primary missing
            if self.backup_dir:
                backup_path = self.backup_dir / cert_filename
                if backup_path.exists():
                    with open(backup_path, "rb") as f:
                        return f.read()
            
            return None
        
        except Exception:
            return None
    
    def get_metadata(self, cert_uuid: str) -> Optional[Dict[str, Any]]:
        """Get certificate metadata."""
        try:
            metadata_path = self.metadata_dir / f"{cert_uuid}.json"
            
            if not metadata_path.exists():
                if not self.backup_metadata_dir:
                    return None
                metadata_path = self.backup_metadata_dir / f"{cert_uuid}.json"
                if not metadata_path.exists():
                    return None
            
            with open(metadata_path, "r") as f:
                return json.load(f)
        
        except Exception:
            return None
    
    def list_certificates(self) -> list[Dict[str, Any]]:
        """List all stored certificates with metadata."""
        certs = []
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    certs.append(metadata)
            except Exception:
                pass
        
        return certs

    def delete_certificate_by_path(self, certificate_path: str) -> bool:
        """Delete a stored certificate and its metadata by stored path."""
        if not certificate_path:
            return True

        try:
            cert_path = Path(certificate_path)
            cert_uuid = cert_path.stem
            stored_filename = cert_path.name

            for base_dir in [self.root_dir, self.backup_dir]:
                if not base_dir:
                    continue
                candidate = Path(base_dir) / stored_filename
                if candidate.exists():
                    candidate.unlink()

            for metadata_dir in [self.metadata_dir, self.backup_metadata_dir]:
                if not metadata_dir:
                    continue
                metadata_path = Path(metadata_dir) / f"{cert_uuid}.json"
                if metadata_path.exists():
                    metadata_path.unlink()

            return True
        except Exception:
            return False

    def copy_certificate_to_folder(self, certificate_path: str, destination_dir: Path) -> Optional[Path]:
        """Copy a stored certificate to a user-facing export folder."""
        if not certificate_path:
            return None

        source = Path(certificate_path)
        if not source.exists():
            source = self.root_dir / source.name

        if not source.exists():
            return None

        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / source.name
        shutil.copy2(source, destination)
        return destination
