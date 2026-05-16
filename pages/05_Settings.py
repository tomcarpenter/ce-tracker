"""
Settings page - Configure compliance cycles, backup locations, and sync status.
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.navigation import render_sidebar_nav

render_sidebar_nav("Settings")
st.title("⚙️ Settings")

storage = st.session_state.get("storage") or Storage()

# Ensure data initialized
storage.initialize()

# Settings file location
settings_file = Path("data/settings.json")

# Load existing settings
def load_settings():
    if settings_file.exists():
        with open(settings_file, "r") as f:
            return json.load(f)
    return {
        "lmhc_start": "2023-01-01",
        "suicide_start": "2020-01-01",
        "equity_start": "2022-01-01",
        "pmhc_start": "2023-01-01",
        "data_backup_path": "backup_data",
        "cert_backup_path": ""
    }

def save_settings(settings):
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)

settings = load_settings()

# Compliance cycle dates
st.subheader("Compliance Cycle Start Dates")

col1, col2 = st.columns(2)

with col1:
    lmhc_start = st.date_input(
        "LMHC Cycle Start (2-year)",
        value=datetime.strptime(settings["lmhc_start"], "%Y-%m-%d").date()
    )
    suicide_start = st.date_input(
        "Suicide Prevention Start (6-year)",
        value=datetime.strptime(settings["suicide_start"], "%Y-%m-%d").date()
    )

with col2:
    equity_start = st.date_input(
        "Equity Cycle Start (4-year)",
        value=datetime.strptime(settings["equity_start"], "%Y-%m-%d").date()
    )
    pmhc_start = st.date_input(
        "PMH-C Cycle Start (2-year)",
        value=datetime.strptime(settings["pmhc_start"], "%Y-%m-%d").date()
    )

st.markdown("---")

# Backup locations
st.subheader("Backup Configuration")

col1, col2 = st.columns(2)

with col1:
    data_backup_path = st.text_input(
        "Data Backup Folder",
        value=settings.get("data_backup_path") or settings.get("csv_backup_path", "backup_data"),
        help="Folder for the backup copy of the local data file"
    )

with col2:
    cert_backup_path = st.text_input(
        "Certificate Backup Folder",
        value=settings.get("cert_backup_path", ""),
        help="External folder for certificate copies (optional)"
    )

st.markdown("---")

# Sync status
st.subheader("Sync & Data Status")

ce_data = storage.load_parquet()
backup_status = storage.backup_status()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Local Records", len(ce_data))

with col2:
    st.metric("Backup Records", backup_status["backup_rows"])

with col3:
    certs_dir = Path("certificates/root")
    cert_count = len(list(certs_dir.glob("*"))) if certs_dir.exists() else 0
    st.metric("Certificates", cert_count)

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Sync Backup Now", use_container_width=True):
        if storage.sync_backup():
            st.success("✓ Backup refreshed")
        else:
            st.warning("Backup sync failed. Check the backup folder path.")

with col2:
    if st.button("📊 View Audit Log", use_container_width=True):
        audit_df = storage.load_parquet()
        if Path("data/audit_log.csv").exists():
            import pandas as pd
            audit = pd.read_csv("data/audit_log.csv")
            st.dataframe(audit.tail(20), use_container_width=True)

st.markdown("---")

# Data export/import
st.subheader("Data Management")

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Export All Data", use_container_width=True):
        ce_data = storage.load_parquet()
        csv_export = ce_data.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv_export,
            file_name="ce_tracker_export.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📤 Import from Backup", use_container_width=True):
        if storage.backup_parquet_path.exists():
            storage.restore_from_backup()
            st.success("✓ Restored local data from backup")
            st.rerun()
        else:
            st.warning("No backup data file found.")

st.markdown("---")

# Save settings
if st.button("💾 Save All Settings", type="primary", use_container_width=True):
    new_settings = {
        "lmhc_start": str(lmhc_start),
        "suicide_start": str(suicide_start),
        "equity_start": str(equity_start),
        "pmhc_start": str(pmhc_start),
        "data_backup_path": data_backup_path,
        "cert_backup_path": cert_backup_path
    }
    save_settings(new_settings)
    st.session_state.storage = Storage(backup_dir=data_backup_path)
    st.session_state.storage.initialize()
    st.success("✓ Settings saved successfully")
