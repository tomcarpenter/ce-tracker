"""
Storage module - Parquet/CSV management and reconciliation.
Source of truth: Parquet
Mirror: CSV
Reconciliation on startup if mismatch detected.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

class Storage:
    """Manage CE records with Parquet truth and CSV mirror."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.parquet_path = self.data_dir / "ce_records.parquet"
        self.csv_path = self.data_dir / "ce_records.csv"
        self.audit_log_path = self.data_dir / "audit_log.csv"
        self.initialized = False
        
        self.data_dir.mkdir(exist_ok=True)
    
    def initialize(self) -> None:
        """Initialize data files if they don't exist."""
        if not self.parquet_path.exists():
            df = pd.DataFrame(columns=[
                "id", "date", "title", "category", "hours", "notes", "certificate_path", 
                "certificate_hash", "created_at", "updated_at"
            ])
            df.to_parquet(self.parquet_path, index=False)
        
        if not self.csv_path.exists():
            df = pd.read_parquet(self.parquet_path)
            df.to_csv(self.csv_path, index=False)
        
        if not self.audit_log_path.exists():
            audit_df = pd.DataFrame(columns=[
                "timestamp", "event_type", "record_id", "details"
            ])
            audit_df.to_csv(self.audit_log_path, index=False)
        
        self.initialized = True
    
    def load_parquet(self) -> pd.DataFrame:
        """Load records from Parquet (source of truth)."""
        if self.parquet_path.exists():
            return pd.read_parquet(self.parquet_path)
        return pd.DataFrame()
    
    def load_csv(self) -> pd.DataFrame:
        """Load records from CSV mirror."""
        if self.csv_path.exists():
            return pd.read_csv(self.csv_path)
        return pd.DataFrame()
    
    def reconciliation_status(self) -> Dict[str, Any]:
        """Check if Parquet and CSV are in sync."""
        parquet_df = self.load_parquet()
        csv_df = self.load_csv()
        
        needs_reconciliation = False
        reason = ""
        
        if len(parquet_df) != len(csv_df):
            needs_reconciliation = True
            reason = f"Row count mismatch: Parquet {len(parquet_df)} vs CSV {len(csv_df)}"
        elif set(parquet_df.columns) != set(csv_df.columns):
            needs_reconciliation = True
            reason = "Column mismatch"
        elif not self._normalize_for_compare(parquet_df).equals(self._normalize_for_compare(csv_df)):
            needs_reconciliation = True
            reason = "Data mismatch"
        
        return {
            "needs_reconciliation": needs_reconciliation,
            "reason": reason,
            "parquet_rows": len(parquet_df),
            "csv_rows": len(csv_df)
        }
    
    def reconciliation_diff(self) -> pd.DataFrame:
        """Show detailed comparison between Parquet and CSV."""
        parquet_df = self.load_parquet()
        csv_df = self.load_csv()
        
        comparison = pd.DataFrame({
            "Source": ["Parquet"] * len(parquet_df) + ["CSV"] * len(csv_df),
            "Record": list(parquet_df.get("id", [])) + list(csv_df.get("id", [])),
            "Date": list(parquet_df.get("date", [])) + list(csv_df.get("date", [])),
            "Title": list(parquet_df.get("title", [])) + list(csv_df.get("title", []))
        })
        
        return comparison
    
    def reconcile_to_parquet(self) -> None:
        """Reconciliation: overwrite CSV from Parquet (safe, recommended)."""
        parquet_df = self.load_parquet()
        parquet_df.to_csv(self.csv_path, index=False)
        self._audit_log("reconciliation", None, "Reconciled to Parquet (safe mode)")
    
    def reconcile_to_csv(self) -> None:
        """Reconciliation: overwrite Parquet from CSV (advanced recovery)."""
        csv_df = self.load_csv()
        csv_df.to_parquet(self.parquet_path, index=False)
        self._audit_log("reconciliation", None, "Reconciled to CSV (recovery mode)")
    
    def write_record(self, record: Dict[str, Any]) -> bool:
        """
        Atomic write to Parquet first, then CSV.
        Rollback on failure.
        """
        previous_df = self.load_parquet()
        previous_csv = self.load_csv()

        try:
            df = previous_df.copy()
            record_id = record.get("id")
            is_update = bool(record_id) and record_id in set(df.get("id", []))
            
            # Add or update record
            if record_id:
                df = df[df["id"] != record["id"]]
            
            new_df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
            
            # Write to Parquet (primary)
            new_df.to_parquet(self.parquet_path, index=False)
            
            # Write to CSV (mirror)
            new_df.to_csv(self.csv_path, index=False)
            
            # Log to audit
            self._audit_log("update" if is_update else "create",
                          record.get("id"), 
                          f"Entry: {record.get('title', 'Untitled')}")
            
            return True
        
        except Exception as e:
            try:
                previous_df.to_parquet(self.parquet_path, index=False)
                previous_csv.to_csv(self.csv_path, index=False)
            except Exception:
                pass
            self._audit_log("error", record.get("id"), str(e))
            return False
    
    def delete_record(self, record_id: str) -> bool:
        """Delete record from Parquet and CSV."""
        try:
            df = self.load_parquet()
            df = df[df["id"] != record_id]
            
            df.to_parquet(self.parquet_path, index=False)
            df.to_csv(self.csv_path, index=False)
            
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

    @staticmethod
    def _normalize_for_compare(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize dtype differences introduced by Parquet/CSV round-trips."""
        normalized = df.copy()
        normalized = normalized.reindex(sorted(normalized.columns), axis=1)

        for column in normalized.columns:
            normalized[column] = normalized[column].fillna("").astype(str)

        if "id" in normalized.columns:
            normalized = normalized.sort_values("id").reset_index(drop=True)
        else:
            normalized = normalized.reset_index(drop=True)

        return normalized
