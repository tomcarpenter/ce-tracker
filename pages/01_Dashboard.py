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

from utils.storage import Storage
from utils.compliance import ComplianceTracker
from utils.navigation import render_sidebar_nav
from utils.ce_export import build_ce_zip

render_sidebar_nav("Dashboard")
st.title("📊 CE Tracking Dashboard")

# Initialize
storage = st.session_state.get("storage") or Storage()
tracker = st.session_state.get("tracker") or ComplianceTracker(storage)

# Ensure data initialized
storage.initialize()

# Load data
ce_data = storage.load_parquet()

st.markdown("---")

def load_settings():
    settings_file = Path("data/settings.json")
    defaults = {
        "lmhc_start": "2023-01-01",
        "suicide_start": "2020-01-01",
        "equity_start": "2022-01-01",
        "pmhc_start": "2023-01-01",
    }
    if not settings_file.exists():
        return defaults

    with open(settings_file, "r") as f:
        loaded_settings = json.load(f)

    defaults.update(loaded_settings)
    return defaults


settings = load_settings()
cycles_config = {
    "LMHC": datetime.strptime(settings["lmhc_start"], "%Y-%m-%d"),
    "Ethics": datetime.strptime(settings["lmhc_start"], "%Y-%m-%d"),
    "Roles": datetime.strptime(settings["lmhc_start"], "%Y-%m-%d"),
    "Suicide": datetime.strptime(settings["suicide_start"], "%Y-%m-%d"),
    "Equity": datetime.strptime(settings["equity_start"], "%Y-%m-%d"),
    "PMH-C": datetime.strptime(settings["pmhc_start"], "%Y-%m-%d"),
}

# Compliance cycles progress
col1, col2 = st.columns(2)

with col1:
    st.subheader("LMHC General (2-Year Cycle)")
    lmhc_status = tracker.get_cycle_status("LMHC", cycles_config["LMHC"])
    progress = lmhc_status["progress_percent"]
    st.progress(progress / 100, text=f"{progress}%")
    st.caption(f"Hours required: {lmhc_status['required_hours']} | Collected: {lmhc_status['collected_hours']}")

with col2:
    st.subheader("Ethics (2-Year Cycle)")
    ethics_status = tracker.get_cycle_status("Ethics", cycles_config["Ethics"])
    progress = ethics_status["progress_percent"]
    st.progress(progress / 100, text=f"{progress}%")
    st.caption(f"Hours required: {ethics_status['required_hours']} | Collected: {ethics_status['collected_hours']}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Roles (2-Year Cycle)")
    roles_status = tracker.get_cycle_status("Roles", cycles_config["Roles"])
    progress = roles_status["progress_percent"]
    st.progress(progress / 100, text=f"{progress}%")
    st.caption(f"Hours required: {roles_status['required_hours']} | Collected: {roles_status['collected_hours']}")

with col2:
    st.subheader("Suicide Prevention (6-Year Cycle)")
    suicide_status = tracker.get_cycle_status("Suicide", cycles_config["Suicide"])
    progress = suicide_status["progress_percent"]
    st.progress(progress / 100, text=f"{progress}%")
    st.caption(f"Hours required: {suicide_status['required_hours']} | Collected: {suicide_status['collected_hours']}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Equity (4-Year Cycle)")
    equity_status = tracker.get_cycle_status("Equity", cycles_config["Equity"])
    progress = equity_status["progress_percent"]
    st.progress(progress / 100, text=f"{progress}%")
    st.caption(f"Hours required: {equity_status['required_hours']} | Collected: {equity_status['collected_hours']}")

with col2:
    st.subheader("PMH-C (2-Year Cycle)")
    pmhc_status = tracker.get_cycle_status("PMH-C", cycles_config["PMH-C"])
    progress = pmhc_status["progress_percent"]
    st.progress(progress / 100, text=f"{progress}%")
    st.caption(f"Hours required: {pmhc_status['required_hours']} | Collected: {pmhc_status['collected_hours']}")

st.markdown("---")

# Recent entries
st.subheader("📋 Recent CE Entries")
if not ce_data.empty:
    st.dataframe(
        ce_data[["date", "title", "category", "hours"]].tail(10),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No CE records yet. Start by adding an entry in the Submission page.")

st.markdown("---")

# PMH-C helper
st.subheader("💡 PMH-C Submission Helper")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Generate PMH-C Copy Text", use_container_width=True):
        if not ce_data.empty and "is_pmhc" in ce_data.columns:
            pmhc_records = ce_data[ce_data["is_pmhc"].fillna(0).astype(bool)]
        else:
            pmhc_records = ce_data
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
            f"{courses_text}\n\n"
            "PMH-C form: https://form.jotform.com/231702468692057\n"
            "Reminder: verify the current form link before submitting."
        )

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

    if not ce_data.empty and "is_pmhc" in ce_data.columns:
        pmhc_export_records = ce_data[ce_data["is_pmhc"].fillna(0).astype(bool)]
    else:
        pmhc_export_records = ce_data.iloc[0:0]

    pmhc_zip, pmhc_record_count, pmhc_file_count = build_ce_zip(
        pmhc_export_records,
        folder_per_record=True,
    )
    st.download_button(
        "Download PMH-C ZIP Packet",
        data=pmhc_zip,
        file_name="pmhc_ce_packet.zip",
        mime="application/zip",
        disabled=pmhc_record_count == 0,
        use_container_width=True,
    )
    if pmhc_record_count:
        st.caption(f"Includes {pmhc_record_count} PMH-C event folders and {pmhc_file_count} attached files.")
    else:
        st.caption("No PMH-C-tagged records available for ZIP export.")
else:
    st.caption("Generate copy-ready text for PMH-C course submission details.")

# Risk alerts
st.subheader("⚠️ Alerts & Notifications")
if not ce_data.empty:
    st.info("✓ All compliance cycles on track. No overdue submissions.")
else:
    st.warning("📌 No CE records found. Add your first entry to get started.")
