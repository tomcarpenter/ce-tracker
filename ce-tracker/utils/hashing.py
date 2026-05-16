"""
Hashing module - File integrity verification.
Compute SHA256 hashes for certificate storage and verification.
"""

import hashlib
from pathlib import Path
from typing import Optional


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """Verify a file matches expected SHA256 hash."""
    computed = compute_file_hash(file_path)
    return computed == expected_hash


def compute_bytes_hash(data: bytes) -> str:
    """Compute SHA256 hash of bytes (for file uploads)."""
    return hashlib.sha256(data).hexdigest()
