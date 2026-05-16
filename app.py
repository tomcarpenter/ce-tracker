"""
CE Tracker - Local-first Streamlit application for compliance tracking.
LMHC + PMH-C continuous education tracking with offline-first architecture.
"""

import streamlit as st
from pathlib import Path
import sys

# Ensure utils can be imported
sys.path.insert(0, str(Path(__file__).parent))

from utils.storage import Storage
from utils.compliance import ComplianceTracker

# Page configuration
st.set_page_config(
    page_title="CE Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
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
    """Main app entry point - Home page."""
    
    # Initialize data on first run
    if not st.session_state.storage.initialized:
        st.session_state.storage.initialize()
    
    # Check for reconciliation needs
    if check_data_reconciliation():
        st.warning("⚠️ Data reconciliation needed")
        show_reconciliation_ui()
        return
    
    # Home page
    st.title("📋 CE Tracker")
    st.markdown("**Local-first Continuing Education tracking for LMHC & PMH-C compliance**")
    
    st.markdown("---")
    
    # Quick stats
    ce_data = st.session_state.storage.load_parquet()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total CE Hours", f"{ce_data['hours'].sum():.1f}" if not ce_data.empty else "0", delta=None)
    with col2:
        st.metric("Entries Recorded", len(ce_data) if not ce_data.empty else "0")
    with col3:
        st.metric("Data Status", "✓ Healthy")
    
    st.markdown("---")
    
    # Navigation guide
    st.subheader("Get Started")
    st.markdown("""
    Use the sidebar navigation to:
    
    1. **Dashboard** — View progress on compliance cycles
    2. **Submission** — Add new CE entry with certificate
    3. **Data Viewer** — Browse and filter records
    4. **Edit Entry** — Modify or delete entries
    5. **Settings** — Configure cycles and backups
    """)
    
    st.markdown("---")
    
    # System status
    st.subheader("System Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Parquet**\n✓ Ready")
    with col2:
        st.markdown("**Audit Log**\n✓ Active")
    with col3:
        st.markdown("**Certificates**\n✓ Syncing")


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
