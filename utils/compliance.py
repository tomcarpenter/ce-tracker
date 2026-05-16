"""
Compliance module - CE requirement tracking and cycle calculations.
Tracks LMHC, Ethics, Roles, Suicide, Equity, and PMH-C compliance cycles.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd


class ComplianceTracker:
    """Track CE requirements across compliance cycles."""

    CATEGORY_FLAGS = {
        "is_lmhc_general": "LMHC General",
        "is_ethics": "Ethics",
        "is_roles": "Roles",
        "is_suicide": "Suicide Prevention",
        "is_equity": "Equity",
        "is_pmhc": "PMH-C",
    }

    def __init__(self, storage):
        self.storage = storage
        self.cycles = {
            "LMHC": {"hours": 32, "years": 2, "flags": ["is_lmhc_general", "is_ethics", "is_roles"]},
            "Ethics": {"hours": 6, "years": 2, "flags": ["is_ethics"]},
            "Roles": {"hours": 2, "years": 2, "flags": ["is_roles"]},
            "Suicide": {"hours": 6, "years": 6, "flags": ["is_suicide"]},
            "Equity": {"hours": 2, "years": 4, "flags": ["is_equity"]},
            "PMH-C": {"hours": 12, "years": 2, "flags": ["is_pmhc"]},
        }
    
    def get_cycle_status(self, cycle_name: str, cycle_start_date: datetime) -> Dict[str, Any]:
        """Get current progress for a compliance cycle."""
        cycle_config = self.cycles.get(cycle_name)
        if not cycle_config:
            return {}
        
        # Calculate cycle end date
        cycle_end = cycle_start_date + timedelta(days=365 * cycle_config["years"])
        
        # Load CE records
        ce_data = self.storage.load_parquet()
        if ce_data.empty:
            collected_hours = 0
        else:
            in_date_range = (
                (pd.to_datetime(ce_data.get("date", [])) >= cycle_start_date) &
                (pd.to_datetime(ce_data.get("date", [])) <= cycle_end)
            )
            flag_filter = self._flag_filter(ce_data, cycle_config["flags"])
            cycle_records = ce_data[in_date_range & flag_filter]
            collected_hours = cycle_records["hours"].sum() if not cycle_records.empty else 0
        
        required_hours = cycle_config["hours"]
        progress_pct = (collected_hours / required_hours * 100) if required_hours > 0 else 0
        
        return {
            "cycle_name": cycle_name,
            "cycle_start": cycle_start_date,
            "cycle_end": cycle_end,
            "days_remaining": (cycle_end - datetime.now()).days,
            "required_hours": required_hours,
            "collected_hours": round(collected_hours, 1),
            "progress_percent": min(int(progress_pct), 100),
            "is_complete": collected_hours >= required_hours,
            "needs_attention": progress_pct < 50 and (cycle_end - datetime.now()).days < 90,
        }
    
    def get_all_cycles_status(self, cycles_config: Dict[str, datetime]) -> list:
        """Get status for all cycles."""
        status = []
        for cycle_name, start_date in cycles_config.items():
            status.append(self.get_cycle_status(cycle_name, start_date))
        return status
    
    def validate_entry(self, entry: Dict[str, Any]) -> tuple[bool, str]:
        """Validate a CE entry for compliance."""
        if not entry.get("title"):
            return False, "Title required"
        
        if not entry.get("date"):
            return False, "Date required"
        
        if entry.get("hours", 0) <= 0:
            return False, "Hours must be greater than 0"
        
        if entry.get("hours", 0) > 40:
            return False, "Hours cannot exceed 40"
        
        selected_flags = [flag for flag in self.CATEGORY_FLAGS if entry.get(flag, 0)]
        if not selected_flags:
            return False, "Select at least one compliance category"

        if entry.get("is_ethics", 0) and entry.get("is_roles", 0):
            return False, "Ethics and Roles cannot overlap on the same CE entry"

        return True, "Valid"

    def category_label(self, entry: Dict[str, Any]) -> str:
        """Create a readable label from category flag columns."""
        selected = [
            label
            for flag, label in self.CATEGORY_FLAGS.items()
            if entry.get(flag, 0)
        ]
        return ", ".join(selected)

    @staticmethod
    def _flag_filter(ce_data: pd.DataFrame, flags: list[str]) -> pd.Series:
        """Return rows where any requested compliance flag is selected."""
        if ce_data.empty:
            return pd.Series(dtype=bool)

        flag_series = pd.Series(False, index=ce_data.index)
        for flag in flags:
            if flag in ce_data.columns:
                flag_series = flag_series | ce_data[flag].fillna(0).astype(bool)

        return flag_series
    
    def generate_pmhc_helper_text(self) -> str:
        """Generate PMH-C submission helper text."""
        return """
**PMH-C Submission Requirements:**
Please include the date each CE course was completed. 
If a certificate does not include the date, please also upload a receipt/confirmation 
of the date for the course.

[Open PMH-C JotForm](https://form.jotform.com/231702468692057)

Verify the current form link is valid before submission.
        """
