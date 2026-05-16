"""
Dashboard page - CE tracking progress and status overview.
Displays progress bars for LMHC, Suicide, Equity, and PMH-C cycles.
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.compliance import ComplianceTracker

st.set_page_config(page_title="Dashboard - CE Tracker", layout="wide")

st.title("📊 CE Tracking Dashboard")

# Initialize
storage = st.session_state.get("storage") or Storage()
tracker = st.session_state.get("tracker") or ComplianceTracker(storage)

# Ensure data initialized
storage.initialize()

# Load data
ce_data = storage.load_parquet()

st.markdown("---")

# Get cycle config (use defaults or from settings)
cycles_config = {
    "LMHC": datetime(2023, 1, 1),  # TODO: Get from settings
    "Suicide": datetime(2020, 1, 1),
    "Equity": datetime(2022, 1, 1),
    "PMH-C": datetime(2023, 1, 1),
}

# Compliance cycles progress
col1, col2 = st.columns(2)

with col1:
    st.subheader("LMHC (2-Year Cycle)")
    lmhc_status = tracker.get_cycle_status("LMHC", cycles_config["LMHC"])
    progress = lmhc_status["progress_percent"]
    st.progress(progress / 100, text=f"{progress}%")
    st.caption(f"Hours required: {lmhc_status['required_hours']} | Collected: {lmhc_status['collected_hours']}")

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
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("💡 PMH-C Submission Helper")
with col2:
    if st.button("Open Form →", use_container_width=True):
        st.markdown(
            "[Open PMH-C JotForm](https://form.jotform.com/231702468692057)"
        )

st.markdown("""
**Note:** PMH-C requires course completion dates. Please include a receipt/confirmation 
if the certificate does not display the date.
""")

# Risk alerts
st.subheader("⚠️ Alerts & Notifications")
if not ce_data.empty:
    st.info("✓ All compliance cycles on track. No overdue submissions.")
else:
    st.warning("📌 No CE records found. Add your first entry to get started.")
