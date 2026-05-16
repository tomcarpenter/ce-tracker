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

def main():
    """Initialize app state, then route to the dashboard."""
    if not st.session_state.storage.initialized:
        st.session_state.storage.initialize()

    runpy.run_path(str(Path(__file__).parent / "pages/01_Dashboard.py"))


if __name__ == "__main__":
    main()
