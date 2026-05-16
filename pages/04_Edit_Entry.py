"""
Edit Entry page - Modify existing CE records.
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.compliance import ComplianceTracker
from utils.navigation import render_sidebar_nav

render_sidebar_nav("Edit Entry")
st.title("✏️ Edit CE Entry")

storage = st.session_state.get("storage") or Storage()
tracker = st.session_state.get("tracker") or ComplianceTracker(storage)

# Ensure data initialized
storage.initialize()

ce_data = storage.load_parquet()

if ce_data.empty:
    st.warning("No CE records to edit.")
    if st.button("Go to Submission"):
        st.switch_page("pages/02_Submission.py")
else:
    # Select entry to edit
    ce_data_copy = ce_data.copy()
    ce_data_copy["label"] = (
        pd.to_datetime(ce_data_copy["date"]).dt.strftime("%Y-%m-%d") + " - " + 
        ce_data_copy.get("title", "Untitled")
    )
    
    selected_label = st.selectbox(
        "Select entry to edit",
        options=ce_data_copy["label"],
        index=None,
        placeholder="Choose an entry..."
    )
    
    if selected_label:
        # Find the selected entry
        idx = ce_data_copy[ce_data_copy["label"] == selected_label].index[0]
        entry = ce_data.loc[idx].to_dict()
        
        st.markdown("---")
        
        # Display current metadata
        with st.expander("Current metadata", expanded=False):
            st.write(f"**ID:** {entry.get('id', 'N/A')}")
            st.write(f"**Created:** {entry.get('created_at', 'N/A')}")
            st.write(f"**Updated:** {entry.get('updated_at', 'N/A')}")
        
        with st.form("ce_edit_form"):
            categories = ["LMHC General", "Suicide Prevention", "Equity", "PMH-C", "Other"]

            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date Completed", value=pd.to_datetime(entry.get("date")))
                title = st.text_input("Course/Training Title", value=entry.get("title", ""))
            
            with col2:
                category = st.selectbox(
                    "Compliance Category",
                    categories,
                    index=categories.index(entry.get("category", "LMHC General"))
                    if entry.get("category", "LMHC General") in categories
                    else 0,
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
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                submitted = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
            
            with col2:
                st.write("")
            
            with col3:
                deleted = st.form_submit_button("🗑️ Delete Entry", type="secondary", use_container_width=True)
            
            if submitted:
                # Update entry
                entry["date"] = date
                entry["title"] = title
                entry["category"] = category
                entry["hours"] = hours
                entry["notes"] = notes
                entry["updated_at"] = datetime.now().isoformat()
                
                success = storage.write_record(entry)
                
                if success:
                    st.success("✓ Entry updated successfully")
                    st.rerun()
                else:
                    st.error("Failed to update entry")
            
            if deleted:
                # Delete entry
                success = storage.delete_record(entry["id"])
                
                if success:
                    st.success("✓ Entry deleted successfully")
                    st.rerun()
                else:
                    st.error("Failed to delete entry")
