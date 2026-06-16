"""
Dashboard page - CE tracking progress and status overview.
Displays progress bars for LMHC, Suicide, Equity, and PMH-C cycles.
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.compliance import ComplianceTracker
from utils.navigation import render_sidebar_nav
from utils.ce_export import build_ce_zip
from utils.app_config import configured_storage

render_sidebar_nav("Dashboard")
st.title("📊 CE Tracking Dashboard")

# Initialize
storage = st.session_state.get("storage") or configured_storage()

# Ensure data initialized
storage.initialize()

# Load data
ce_data = storage.load_parquet()

st.markdown("---")

def load_settings():
    settings_file = storage.settings_path
    defaults = {
        "lmhc_start": "2023-01-01",
        "suicide_start": "2020-01-01",
        "equity_start": "2022-01-01",
        "pmhc_start": "2023-01-01",
        "requirements": ComplianceTracker.DEFAULT_REQUIREMENTS,
    }
    if not settings_file.exists():
        return defaults

    with open(settings_file, "r") as f:
        loaded_settings = json.load(f)

    defaults.update(loaded_settings)
    defaults["requirements"] = ComplianceTracker.DEFAULT_REQUIREMENTS | loaded_settings.get("requirements", {})
    return defaults


settings = load_settings()
tracker = ComplianceTracker(storage, requirements=settings["requirements"])
cycles_config = {
    "LMHC": datetime.strptime(settings["lmhc_start"], "%Y-%m-%d"),
    "Ethics": datetime.strptime(settings["lmhc_start"], "%Y-%m-%d"),
    "Roles": datetime.strptime(settings["lmhc_start"], "%Y-%m-%d"),
    "Suicide": datetime.strptime(settings["suicide_start"], "%Y-%m-%d"),
    "Equity": datetime.strptime(settings["equity_start"], "%Y-%m-%d"),
    "PMH-C": datetime.strptime(settings["pmhc_start"], "%Y-%m-%d"),
}

if "dashboard_cycle_offsets" not in st.session_state:
    st.session_state.dashboard_cycle_offsets = {}

st.caption("Each counter counts only CE records completed inside its displayed date range.")


def render_cycle_status(title: str, cycle_name: str, cycle_start: datetime) -> dict:
    cycle_offset = get_cycle_offset(cycle_name)
    status = tracker.get_cycle_status(
        cycle_name,
        cycle_start,
        cycle_offset=cycle_offset,
    )
    progress = status["progress_percent"]
    start_label = status["cycle_start"].strftime("%Y-%m-%d")
    end_label = status["cycle_end"].strftime("%Y-%m-%d")

    st.subheader(title)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Previous", key=f"{cycle_name}_previous_cycle", use_container_width=True):
            set_cycle_offset(cycle_name, cycle_offset - 1)
            st.rerun()
    with col2:
        if st.button("Current", key=f"{cycle_name}_current_cycle", use_container_width=True):
            set_cycle_offset(cycle_name, 0)
            st.rerun()
    with col3:
        if st.button("Next →", key=f"{cycle_name}_next_cycle", use_container_width=True):
            set_cycle_offset(cycle_name, cycle_offset + 1)
            st.rerun()

    if cycle_offset:
        st.caption(f"Showing {abs(cycle_offset)} cycle{'s' if abs(cycle_offset) != 1 else ''} {'future' if cycle_offset > 0 else 'past'}.")

    st.progress(progress / 100, text=f"{progress}%")
    st.caption(
        f"Required: {status['required_hours']} | Collected: {status['collected_hours']} | "
        f"Range: {start_label} through {end_label}"
    )

    return status


def get_cycle_offset(cycle_name: str) -> int:
    return st.session_state.dashboard_cycle_offsets.get(f"{cycle_name}_offset", 0)


def set_cycle_offset(cycle_name: str, offset: int) -> None:
    st.session_state.dashboard_cycle_offsets[f"{cycle_name}_offset"] = offset


def filtered_pmhc_records(data: pd.DataFrame, status: dict) -> pd.DataFrame:
    if data.empty or "is_pmhc" not in data.columns:
        return data.iloc[0:0]

    pmhc_dates = pd.to_datetime(data["date"])
    return data[
        data["is_pmhc"].fillna(0).astype(bool)
        & (pmhc_dates >= status["cycle_start"])
        & (pmhc_dates <= status["cycle_end"])
    ]


# Compliance cycles progress
col1, col2 = st.columns(2)

with col1:
    lmhc_status = render_cycle_status("LMHC General (2-Year Cycle)", "LMHC", cycles_config["LMHC"])

with col2:
    ethics_status = render_cycle_status("Ethics (2-Year Cycle)", "Ethics", cycles_config["Ethics"])

col1, col2 = st.columns(2)

with col1:
    roles_status = render_cycle_status("Roles (2-Year Cycle)", "Roles", cycles_config["Roles"])

with col2:
    suicide_status = render_cycle_status("Suicide Prevention (6-Year Cycle)", "Suicide", cycles_config["Suicide"])

col1, col2 = st.columns(2)

with col1:
    equity_status = render_cycle_status("Equity (4-Year Cycle)", "Equity", cycles_config["Equity"])

with col2:
    pmhc_status = render_cycle_status("PMH-C (2-Year Cycle)", "PMH-C", cycles_config["PMH-C"])

st.markdown("---")

# Recent entries
st.subheader("📋 Recent CE Entries")
if not ce_data.empty:
    st.dataframe(
        ce_data[["date", "title", "trainer_name", "organization", "category", "hours"]].tail(10),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No CE records yet. Start by adding an entry in the Submission page.")

st.markdown("---")

# PMH-C helper
st.subheader("💡 PMH-C Submission Helper")

pmhc_start_label = pmhc_status["cycle_start"].strftime("%Y-%m-%d")
pmhc_end_label = pmhc_status["cycle_end"].strftime("%Y-%m-%d")
pmhc_cycle_label = f"{pmhc_start_label} through {pmhc_end_label}"
pmhc_cycle_offset = get_cycle_offset("PMH-C")

st.caption(f"PMH-C export period: {pmhc_cycle_label}")
pmhc_col1, pmhc_col2, pmhc_col3 = st.columns(3)
with pmhc_col1:
    if st.button("Previous PMH-C Cycle", key="pmhc_export_previous_cycle", use_container_width=True):
        set_cycle_offset("PMH-C", pmhc_cycle_offset - 1)
        st.rerun()
with pmhc_col2:
    if st.button("Current PMH-C Cycle", key="pmhc_export_current_cycle", use_container_width=True):
        set_cycle_offset("PMH-C", 0)
        st.rerun()
with pmhc_col3:
    if st.button("Next PMH-C Cycle", key="pmhc_export_next_cycle", use_container_width=True):
        set_cycle_offset("PMH-C", pmhc_cycle_offset + 1)
        st.rerun()

if st.session_state.get("pmhc_helper_cycle_label") != pmhc_cycle_label:
    st.session_state.pop("pmhc_helper_text", None)

pmhc_export_records = filtered_pmhc_records(ce_data, pmhc_status)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Generate PMH-C Copy Text", use_container_width=True):
        pmhc_records = pmhc_export_records
        course_lines = []

        if not pmhc_records.empty:
            pmhc_records = pmhc_records.sort_values("date")
            for _, record in pmhc_records.iterrows():
                completed = pd.to_datetime(record.get("date")).strftime("%Y-%m-%d")
                course_lines.append(
                    f"- {completed}: {record.get('title', 'Untitled')} ({record.get('hours', 0)} hours)"
                )

        courses_text = "\n".join(course_lines) if course_lines else "- Add PMH-C course names and completion dates here."
        st.session_state.pmhc_helper_text = (
            "Training/Course Names: Please include the date each CE course was completed. "
            "If a certificate does not include the date, please also upload a receipt/confirmation "
            "of the date for the course.\n\n"
            f"Selected PMH-C cycle: {pmhc_cycle_label}\n\n"
            f"{courses_text}\n\n"
            "PMH-C form: https://form.jotform.com/231702468692057\n"
            "Reminder: verify the current form link before submitting."
        )
        st.session_state.pmhc_helper_cycle_label = pmhc_cycle_label

with col2:
    st.link_button(
        "Open PMH-C Form",
        "https://form.jotform.com/231702468692057",
        use_container_width=True,
    )

if st.session_state.get("pmhc_helper_text"):
    st.text_area(
        "Copy-ready PMH-C text",
        value=st.session_state.pmhc_helper_text,
        height=220,
    )

else:
    st.caption("Generate copy-ready text for PMH-C course submission details.")

pmhc_zip, pmhc_record_count, pmhc_file_count = build_ce_zip(
    pmhc_export_records,
    folder_per_record=True,
    certificate_root_dir=storage.certificate_root_dir,
    metadata_dir=storage.certificate_metadata_dir,
)
st.download_button(
    "Download PMH-C ZIP Packet",
    data=pmhc_zip,
    file_name=f"pmhc_ce_packet_{pmhc_start_label}_to_{pmhc_end_label}.zip",
    mime="application/zip",
    disabled=pmhc_record_count == 0,
    use_container_width=True,
)
if pmhc_record_count:
    st.caption(
        f"Includes {pmhc_record_count} PMH-C event folders and {pmhc_file_count} attached files "
        f"for {pmhc_cycle_label}."
    )
else:
    st.caption(f"No PMH-C-tagged records available for {pmhc_cycle_label}.")

# Risk alerts
st.subheader("⚠️ Alerts & Notifications")
if not ce_data.empty:
    st.info("✓ All compliance cycles on track. No overdue submissions.")
else:
    st.warning("📌 No CE records found. Add your first entry to get started.")
