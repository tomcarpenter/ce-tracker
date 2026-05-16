"""
Edit Entry page - Modify existing CE records.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.compliance import ComplianceTracker

st.set_page_config(page_title="Edit Entry - CE Tracker", layout="wide")

st.title("✏️ Edit CE Entry")

storage = st.session_state.get("storage") or Storage()
tracker = st.session_state.get("tracker") or ComplianceTracker(storage)

ce_data = storage.load_parquet()

if ce_data.empty:
    st.warning("No CE records to edit.")
else:
    # Select entry to edit
    ce_data_with_labels = ce_data.copy()
    ce_data_with_labels["label"] = (
        ce_data_with_labels["date"].astype(str) + " - " + 
        ce_data_with_labels.get("title", "Untitled")
    )
    
    selected_entry = st.selectbox(
        "Select entry to edit",
        options=ce_data_with_labels["label"],
        index=None
    )
    
    if selected_entry:
        # Find and load the entry
        idx = ce_data_with_labels[ce_data_with_labels["label"] == selected_entry].index[0]
        entry = ce_data.loc[idx]
        
        st.markdown("---")
        
        with st.form("ce_edit_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date Completed", value=entry.get("date", None))
                title = st.text_input("Course/Training Title", value=entry.get("title", ""))
            
            with col2:
                category = st.selectbox(
                    "Compliance Category",
                    ["LMHC General", "Suicide Prevention", "Equity", "PMH-C", "Other"],
                    index=0
                )
                hours = st.number_input(
                    "CE Hours",
                    min_value=0.0,
                    max_value=40.0,
                    step=0.5,
                    value=float(entry.get("hours", 0))
                )
            
            notes = st.text_area(
                "Additional Notes",
                height=100,
                value=entry.get("notes", "")
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
            
            with col2:
                deleted = st.form_submit_button("Delete Entry", type="secondary", use_container_width=True)
            
            if submitted:
                # TODO: Update in storage
                st.success("✓ Entry updated")
            
            if deleted:
                # TODO: Delete from storage
                st.warning("✓ Entry deleted")
