"""
Storage module - local Parquet source plus separate-folder backup mirror.
Source of truth: data/ce_records.parquet
Backup: backup_data/ce_records.parquet by default, configurable in settings.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import json
import shutil

from utils.ce_export import write_ce_folders


CATEGORY_FLAG_COLUMNS = [
    "is_lmhc_general",
    "is_ethics",
    "is_roles",
    "is_suicide",
    "is_equity",
    "is_pmhc",
]

CATEGORY_LABELS = {
    "is_lmhc_general": "LMHC General",
    "is_ethics": "Ethics",
    "is_roles": "Roles",
    "is_suicide": "Suicide Prevention",
    "is_equity": "Equity",
    "is_pmhc": "PMH-C",
}


class Storage:
    """Manage CE records with one local source and one backup mirror."""
    
    def __init__(self, data_dir: str = "data", backup_dir: Optional[str] = None):
        self.data_dir = Path(data_dir)
        self.parquet_path = self.data_dir / "ce_records.parquet"
        self.audit_log_path = self.data_dir / "audit_log.csv"
        self.settings_path = self.data_dir / "settings.json"
        self.backup_dir = Path(backup_dir) if backup_dir else self._configured_backup_dir()
        self.backup_parquet_path = self.backup_dir / "ce_records.parquet"
        self.backup_csv_path = self.backup_dir / "ce_records.csv"
        self.backup_audit_log_path = self.backup_dir / "audit_log.csv"
        self.backup_settings_path = self.backup_dir / "settings.json"
        self.backup_events_dir = self.backup_dir / "events"
        self.initialized = False
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> None:
        """Initialize data files if they don't exist."""
        if not self.parquet_path.exists():
            df = pd.DataFrame(columns=self._schema_columns())
            df.to_parquet(self.parquet_path, index=False)
        
        if not self.audit_log_path.exists():
            audit_df = pd.DataFrame(columns=[
                "timestamp", "event_type", "record_id", "details"
            ])
            audit_df.to_csv(self.audit_log_path, index=False)

        self.sync_backup()
        
        self.initialized = True
    
    def load_parquet(self) -> pd.DataFrame:
        """Load records from Parquet (source of truth)."""
        if self.parquet_path.exists():
            try:
                return self._normalize_records(pd.read_parquet(self.parquet_path))
            except Exception:
                if self.backup_parquet_path.exists():
                    return self._normalize_records(pd.read_parquet(self.backup_parquet_path))
                raise
        return pd.DataFrame()
    
    def restore_from_backup(self) -> None:
        """Restore local source from backup."""
        backup_df = self.load_backup()
        backup_df.to_parquet(self.parquet_path, index=False)
        self._audit_log("backup_restore", None, "Local data restored from backup")
    
    def write_record(self, record: Dict[str, Any]) -> bool:
        """
        Atomic write to local Parquet first, then backup mirror.
        Rollback on failure.
        """
        previous_df = self.load_parquet()
        previous_backup = self.load_backup()

        try:
            df = previous_df.copy()
            record_id = record.get("id")
            is_update = bool(record_id) and record_id in set(df.get("id", []))
            record = self._normalize_record(record)
            
            # Add or update record
            if record_id:
                df = df[df["id"] != record["id"]]
            
            new_df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
            
            # Write to Parquet (primary)
            new_df.to_parquet(self.parquet_path, index=False)
            
            self.sync_backup()
            
            # Log to audit
            self._audit_log("update" if is_update else "create",
                          record.get("id"), 
                          f"Entry: {record.get('title', 'Untitled')}")
            
            return True
        
        except Exception as e:
            try:
                previous_df.to_parquet(self.parquet_path, index=False)
                previous_backup.to_parquet(self.backup_parquet_path, index=False)
            except Exception:
                pass
            self._audit_log("error", record.get("id"), str(e))
            return False
    
    def delete_record(self, record_id: str) -> bool:
        """Delete record from local Parquet, then update backup mirror."""
        try:
            df = self.load_parquet()
            df = df[df["id"] != record_id]
            
            df.to_parquet(self.parquet_path, index=False)
            self.sync_backup()
            
            self._audit_log("delete", record_id, "Record deleted")
            return True
        
        except Exception as e:
            self._audit_log("error", record_id, str(e))
            return False
    
    def _audit_log(self, event_type: str, record_id: Optional[str], details: str) -> None:
        """Append to audit log."""
        from datetime import datetime
        
        new_entry = pd.DataFrame([{
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "record_id": record_id or "",
            "details": details
        }])
        
        if self.audit_log_path.exists():
            audit_df = pd.read_csv(self.audit_log_path)
            audit_df = pd.concat([audit_df, new_entry], ignore_index=True)
        else:
            audit_df = new_entry
        
        audit_df.to_csv(self.audit_log_path, index=False)
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.audit_log_path, self.backup_audit_log_path)
        except Exception:
            pass

    def load_backup(self) -> pd.DataFrame:
        """Load records from the backup mirror."""
        if self.backup_parquet_path.exists():
            return self._normalize_records(pd.read_parquet(self.backup_parquet_path))
        return pd.DataFrame(columns=self._schema_columns())

    def sync_backup(self) -> bool:
        """Mirror the local source files into the configured backup folder."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            if self.parquet_path.exists():
                shutil.copy2(self.parquet_path, self.backup_parquet_path)
                backup_records = self.load_parquet()
                backup_records.to_csv(self.backup_csv_path, index=False)
                if self.backup_events_dir.exists():
                    shutil.rmtree(self.backup_events_dir)
                write_ce_folders(backup_records, self.backup_events_dir)
            if self.audit_log_path.exists():
                shutil.copy2(self.audit_log_path, self.backup_audit_log_path)
            if self.settings_path.exists():
                shutil.copy2(self.settings_path, self.backup_settings_path)
            return True
        except Exception:
            return False

    def backup_status(self) -> Dict[str, Any]:
        local_rows = len(self.load_parquet())
        backup_rows = len(self.load_backup())

        return {
            "backup_dir": str(self.backup_dir),
            "backup_exists": self.backup_parquet_path.exists(),
            "local_rows": local_rows,
            "backup_rows": backup_rows,
            "event_folders": len(list(self.backup_events_dir.iterdir())) if self.backup_events_dir.exists() else 0,
            "settings_backed_up": self.backup_settings_path.exists(),
            "in_sync": self.backup_parquet_path.exists() and local_rows == backup_rows,
        }

    @staticmethod
    def _normalize_for_compare(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize dtype differences introduced by storage round-trips."""
        normalized = df.copy()
        normalized = normalized.reindex(sorted(normalized.columns), axis=1)

        for column in normalized.columns:
            normalized[column] = normalized[column].fillna("").astype(str)

        if "id" in normalized.columns:
            normalized = normalized.sort_values("id").reset_index(drop=True)
        else:
            normalized = normalized.reset_index(drop=True)

        return normalized

    @staticmethod
    def _schema_columns() -> list[str]:
        return [
            "id",
            "date",
            "title",
            *CATEGORY_FLAG_COLUMNS,
            "category",
            "hours",
            "notes",
            "certificate_path",
            "certificate_hash",
            "created_at",
            "updated_at",
        ]

    @classmethod
    def _normalize_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(record)

        legacy_category = str(normalized.get("category", ""))
        if legacy_category:
            legacy_map = {
                "LMHC General": "is_lmhc_general",
                "Ethics": "is_ethics",
                "Roles": "is_roles",
                "Suicide Prevention": "is_suicide",
                "Equity": "is_equity",
                "PMH-C": "is_pmhc",
            }
            for label, flag in legacy_map.items():
                if label in legacy_category and flag not in normalized:
                    normalized[flag] = 1

        for flag in CATEGORY_FLAG_COLUMNS:
            normalized[flag] = cls._flag_value(normalized.get(flag, 0))

        normalized["category"] = ", ".join(
            label for flag, label in CATEGORY_LABELS.items() if normalized.get(flag, 0)
        )

        return normalized

    @classmethod
    def _normalize_records(cls, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=cls._schema_columns())

        normalized = pd.DataFrame(
            [cls._normalize_record(record) for record in df.to_dict("records")]
        )

        for column in cls._schema_columns():
            if column not in normalized.columns:
                normalized[column] = ""

        return normalized[cls._schema_columns()]

    @staticmethod
    def _flag_value(value: Any) -> int:
        if pd.isna(value):
            return 0

        if isinstance(value, str):
            return 1 if value.strip().lower() in {"1", "true", "yes", "y"} else 0

        return int(bool(value))

    def _configured_backup_dir(self) -> Path:
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                configured_path = settings.get("data_backup_path") or settings.get("csv_backup_path")
                if configured_path:
                    return Path(configured_path)
            except Exception:
                pass

        return Path("backup_data")
