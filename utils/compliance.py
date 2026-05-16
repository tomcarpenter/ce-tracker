"""
Compliance module - CE requirement tracking and cycle calculations.
Tracks LMHC, Suicide, Equity, and PMH-C compliance cycles.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd


class ComplianceTracker:
    """Track CE requirements across compliance cycles."""
    
    # Requirement definitions (hours per cycle)
    REQUIREMENTS = {
        "LMHC General": {"hours": 40, "cycle_years": 2},
        "Suicide Prevention": {"hours": 6, "cycle_years": 6},
        "Equity": {"hours": 6, "cycle_years": 4},
        "PMH-C": {"hours": 60, "cycle_years": 2},
        "Other": {"hours": 0, "cycle_years": 0},
    }
    
    def __init__(self, storage):
        self.storage = storage
        self.cycles = {
            "LMHC": {"hours": 40, "years": 2},
            "Suicide": {"hours": 6, "years": 6},
            "Equity": {"hours": 6, "years": 4},
            "PMH-C": {"hours": 60, "years": 2},
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
            # Filter records in cycle date range by category matching
            category_filter = cycle_name if cycle_name != "PMH-C" else "PMH-C"
            cycle_records = ce_data[
                (pd.to_datetime(ce_data.get("date", [])) >= cycle_start_date) &
                (pd.to_datetime(ce_data.get("date", [])) <= cycle_end) &
                (ce_data.get("category", "").str.contains(category_filter, case=False, na=False))
            ]
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
        
        category = entry.get("category", "")
        if category not in self.REQUIREMENTS:
            return False, f"Invalid category: {category}"
        
        return True, "Valid"
    
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
