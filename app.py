from pathlib import Path
import runpy
import sys

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from utils.compliance import ComplianceTracker
from utils.storage import Storage

st.set_page_config(
    page_title="CE Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "storage" not in st.session_state:
    st.session_state.storage = Storage()

if "tracker" not in st.session_state:
    st.session_state.tracker = ComplianceTracker(st.session_state.storage)

if "reconciliation_pending" not in st.session_state:
    st.session_state.reconciliation_pending = False


def check_data_reconciliation():
    """
    On startup: verify Parquet vs CSV alignment.
    If mismatch: prompt user for reconciliation decision.
    """
    storage = st.session_state.storage
    status = storage.reconciliation_status()
    
    if status["needs_reconciliation"]:
        st.session_state.reconciliation_pending = True
        return True
    return False


def main():
    """Initialize app state, handle reconciliation, then route to pages."""
    if not st.session_state.storage.initialized:
        st.session_state.storage.initialize()

    if check_data_reconciliation():
        st.warning("⚠️ Data reconciliation needed")
        show_reconciliation_ui()
        return

    runpy.run_path(str(Path(__file__).parent / "pages/01_Dashboard.py"))


def show_reconciliation_ui():
    """Display reconciliation UI when Parquet/CSV mismatch detected."""
    st.error("### Data Reconciliation Required")
    st.markdown("""
    A mismatch was detected between your primary data store (Parquet) and backup (CSV).
    Please choose how to resolve this:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✓ Use Parquet (Recommended Safe Option)", use_container_width=True):
            st.session_state.storage.reconcile_to_parquet()
            st.session_state.reconciliation_pending = False
            st.rerun()
    
    with col2:
        if st.button("⚠️ Use CSV (Advanced Recovery)", use_container_width=True):
            st.session_state.storage.reconcile_to_csv()
            st.session_state.reconciliation_pending = False
            st.rerun()
    
    # Show diff
    with st.expander("View detailed comparison"):
        diff = st.session_state.storage.reconciliation_diff()
        st.dataframe(diff, use_container_width=True)


if __name__ == "__main__":
    main()
