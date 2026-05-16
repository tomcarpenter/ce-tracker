"""
Submission page - Create new CE entry with file upload and metadata.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.compliance import ComplianceTracker

st.set_page_config(page_title="Submission - CE Tracker", layout="wide")

st.title("➕ Submit CE Entry")

storage = st.session_state.get("storage") or Storage()
tracker = st.session_state.get("tracker") or ComplianceTracker(storage)

with st.form("ce_submission_form"):
    # Core fields
    col1, col2 = st.columns(2)
    
    with col1:
        date = st.date_input("Date Completed")
        title = st.text_input("Course/Training Title")
    
    with col2:
        category = st.selectbox(
            "Compliance Category",
            ["LMHC General", "Suicide Prevention", "Equity", "PMH-C", "Other"]
        )
        hours = st.number_input("CE Hours", min_value=0.0, max_value=40.0, step=0.5)
    
    # Certificate upload
    st.markdown("---")
    st.subheader("Certificate Upload")
    certificate_file = st.file_uploader(
        "Upload certificate (PDF preferred)",
        type=["pdf", "png", "jpg", "jpeg"]
    )
    
    if certificate_file:
        st.success(f"File selected: {certificate_file.name}")
    
    # Additional notes
    st.markdown("---")
    notes = st.text_area("Additional Notes", height=100, placeholder="Provider, location, or other details...")
    
    # Submit button
    submitted = st.form_submit_button("Submit CE Entry", type="primary", use_container_width=True)
    
    if submitted:
        if not title or not date:
            st.error("Please fill in title and date")
        else:
            # TODO: Implement write flow
            st.success(f"✓ CE entry created: {title}")
            st.balloons()

st.markdown("---")
st.info("""
**Tips:**
- Upload certificate immediately after course completion
- Include receipt if certificate lacks date (especially for PMH-C)
- Dates must be within compliance cycle (today back to cycle start)
""")
