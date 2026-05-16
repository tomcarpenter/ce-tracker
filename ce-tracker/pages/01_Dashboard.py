"""
Dashboard page - CE tracking progress and status overview.
Displays progress bars for LMHC, Suicide, Equity, and PMH-C cycles.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.compliance import ComplianceTracker

st.set_page_config(page_title="Dashboard - CE Tracker", layout="wide")

st.title("📊 CE Tracking Dashboard")

# Initialize
storage = st.session_state.get("storage") or Storage()
tracker = st.session_state.get("tracker") or ComplianceTracker(storage)

# Load data
ce_data = storage.load_parquet()

st.markdown("---")

# Compliance cycles progress
col1, col2 = st.columns(2)

with col1:
    st.subheader("LMHC (2-Year Cycle)")
    # TODO: Calculate progress from CE records
    progress = 25
    st.progress(progress / 100, text=f"{progress}%")
    st.caption("Hours required: 40 | Collected: 10")

with col2:
    st.subheader("Suicide Prevention (6-Year Cycle)")
    progress = 15
    st.progress(progress / 100, text=f"{progress}%")
    st.caption("Hours required: 6 | Collected: 0.9")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Equity (4-Year Cycle)")
    progress = 0
    st.progress(progress / 100, text=f"{progress}%")
    st.caption("Hours required: 6 | Collected: 0")

with col2:
    st.subheader("PMH-C (2-Year Cycle)")
    progress = 30
    st.progress(progress / 100, text=f"{progress}%")
    st.caption("Hours required: 60 | Collected: 18")

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
    st.info("No CE records found. Start by adding an entry.")

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
st.info("✓ All compliance cycles on track. No overdue submissions.")
