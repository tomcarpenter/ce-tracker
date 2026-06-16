"""
Settings page - Configure compliance cycles, backup locations, and sync status.
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json
import platform
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.compliance import ComplianceTracker
from utils.navigation import render_sidebar_nav
from utils.app_config import configured_storage, save_app_config

render_sidebar_nav("Settings")
st.title("⚙️ Settings")

selected_data_folder = st.session_state.pop("selected_data_folder", None)
if selected_data_folder:
    save_app_config({"data_dir": selected_data_folder})
    st.session_state.data_dir = selected_data_folder
    st.session_state.pop("storage", None)
    st.session_state.pop("tracker", None)

storage = st.session_state.get("storage") or configured_storage()

# Ensure data initialized
storage.initialize()

# Settings file location
settings_file = storage.settings_path

# Load existing settings
def load_settings():
    defaults = {
        "lmhc_start": "2023-01-01",
        "suicide_start": "2020-01-01",
        "equity_start": "2022-01-01",
        "pmhc_start": "2023-01-01",
        "data_backup_path": "backup_data",
        "requirements": ComplianceTracker.DEFAULT_REQUIREMENTS,
    }

    if settings_file.exists():
        with open(settings_file, "r") as f:
            loaded = json.load(f)
        defaults.update(loaded)
        defaults["requirements"] = ComplianceTracker.DEFAULT_REQUIREMENTS | loaded.get("requirements", {})

    return defaults

def save_settings(settings, target_settings_file: Path = settings_file):
    target_settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_settings_file, "w") as f:
        json.dump(settings, f, indent=2)

settings = load_settings()


def choose_folder(prompt: str) -> str | None:
    """Open a local folder picker."""
    if platform.system() == "Darwin":
        script = (
            'POSIX path of (choose folder with prompt '
            f'"{prompt}")'
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout.strip() or None

            if result.stderr and "User canceled" not in result.stderr:
                st.warning(f"Folder picker unavailable: {result.stderr.strip()}")
            return None
        except Exception as exc:
            st.warning(f"macOS folder picker unavailable: {exc}")

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title=prompt)
        root.destroy()
        return folder or None
    except Exception as exc:
        st.warning(f"Folder picker unavailable: {exc}")
        return None

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

st.subheader("Required CE Credits")
requirements = settings["requirements"]

col1, col2, col3 = st.columns(3)

with col1:
    lmhc_required = st.number_input(
        "LMHC General Required",
        min_value=0.0,
        max_value=200.0,
        step=0.5,
        value=float(requirements["LMHC"]),
    )
    ethics_required = st.number_input(
        "Ethics Required",
        min_value=0.0,
        max_value=200.0,
        step=0.5,
        value=float(requirements["Ethics"]),
    )

with col2:
    roles_required = st.number_input(
        "Roles Required",
        min_value=0.0,
        max_value=200.0,
        step=0.5,
        value=float(requirements["Roles"]),
    )
    suicide_required = st.number_input(
        "Suicide Prevention Required",
        min_value=0.0,
        max_value=200.0,
        step=0.5,
        value=float(requirements["Suicide"]),
    )

with col3:
    equity_required = st.number_input(
        "Equity Required",
        min_value=0.0,
        max_value=200.0,
        step=0.5,
        value=float(requirements["Equity"]),
    )
    pmhc_required = st.number_input(
        "PMH-C Required",
        min_value=0.0,
        max_value=200.0,
        step=0.5,
        value=float(requirements["PMH-C"]),
    )

st.markdown("---")

# Backup locations
st.subheader("Storage Locations")

if "data_dir" not in st.session_state:
    st.session_state.data_dir = str(storage.data_dir)

if "data_backup_path" not in st.session_state:
    st.session_state.data_backup_path = (
        settings.get("data_backup_path") or settings.get("csv_backup_path", "backup_data")
    )

if st.session_state.get("selected_backup_folder"):
    st.session_state.data_backup_path = st.session_state.pop("selected_backup_folder")

data_col1, data_col2 = st.columns([3, 1])

with data_col1:
    data_dir = st.text_input(
        "Data Folder",
        key="data_dir",
        help="The app will read and write ce_records.parquet, audit_log.csv, and settings.json in this folder"
    )

with data_col2:
    st.write("")
    st.write("")
    if st.button("Browse...", key="browse_data_dir", use_container_width=True):
        selected_folder = choose_folder("Choose CE Tracker data folder")
        if selected_folder:
            st.session_state.selected_data_folder = selected_folder
            st.rerun()

backup_col1, backup_col2 = st.columns([3, 1])

with backup_col1:
    data_backup_path = st.text_input(
        "Data Backup Folder",
        key="data_backup_path",
        help="The app will maintain records, settings, and event folders in this location"
    )

with backup_col2:
    st.write("")
    st.write("")
    if st.button("Browse...", key="browse_backup_dir", use_container_width=True):
        selected_folder = choose_folder("Choose CE Tracker backup folder")
        if selected_folder:
            st.session_state.selected_backup_folder = selected_folder
            st.rerun()

st.caption("The data folder is the source of truth. Backup is automatic after submissions, edits, deletes, and settings changes. The backup folder contains ce_records.parquet, settings.json, and an events folder with one subfolder per CE event.")

st.markdown("---")

st.subheader("Backup Status")

ce_data = storage.load_parquet()
backup_status = storage.backup_status()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Local Records", len(ce_data))

with col2:
    st.metric("Backup Records", backup_status["backup_rows"])

with col3:
    st.metric("Event Folders", backup_status["event_folders"])

with col4:
    st.metric("Settings Backup", "Yes" if backup_status["settings_backed_up"] else "No")

st.markdown("---")

if st.button("📊 View Audit Log", use_container_width=True):
    if storage.audit_log_path.exists():
        import pandas as pd
        audit = pd.read_csv(storage.audit_log_path)
        st.dataframe(audit.tail(20), use_container_width=True)

st.markdown("---")

# Save settings
if st.button("💾 Save All Settings", type="primary", use_container_width=True):
    next_storage = Storage(data_dir=data_dir, backup_dir=data_backup_path)
    new_settings = {
        "data_dir": data_dir,
        "lmhc_start": str(lmhc_start),
        "suicide_start": str(suicide_start),
        "equity_start": str(equity_start),
        "pmhc_start": str(pmhc_start),
        "data_backup_path": data_backup_path,
        "requirements": {
            "LMHC": lmhc_required,
            "Ethics": ethics_required,
            "Roles": roles_required,
            "Suicide": suicide_required,
            "Equity": equity_required,
            "PMH-C": pmhc_required,
        },
    }
    save_app_config({"data_dir": data_dir})
    save_settings(new_settings, next_storage.settings_path)
    st.session_state.storage = next_storage
    st.session_state.storage.initialize()
    st.session_state.tracker = ComplianceTracker(
        st.session_state.storage,
        requirements=new_settings["requirements"],
    )
    st.success("✓ Settings saved successfully")
