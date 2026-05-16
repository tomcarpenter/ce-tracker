"""
Data Viewer page - Browse, filter, and inspect CE records.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage

st.set_page_config(page_title="Data Viewer - CE Tracker", layout="wide")

st.title("🔍 Data Viewer")

storage = st.session_state.get("storage") or Storage()

# Load data
ce_data = storage.load_parquet()

if ce_data.empty:
    st.info("No CE records found.")
else:
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_category = st.multiselect(
            "Category",
            options=ce_data["category"].unique() if "category" in ce_data.columns else [],
            default=None
        )
    
    with col2:
        date_range = st.date_input(
            "Date Range",
            value=(ce_data["date"].min(), ce_data["date"].max()) if "date" in ce_data.columns else None
        )
    
    with col3:
        search_text = st.text_input("Search title", placeholder="Type to filter...")
    
    # Apply filters
    filtered = ce_data.copy()
    
    if selected_category:
        filtered = filtered[filtered["category"].isin(selected_category)]
    
    if search_text:
        filtered = filtered[filtered["title"].str.contains(search_text, case=False, na=False)]
    
    # Display table
    st.markdown("---")
    st.subheader(f"Records: {len(filtered)}")
    
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "hours": st.column_config.NumberColumn(format="%.1f"),
        }
    )
    
    # Actions
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export to CSV"):
            csv = filtered.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="ce_records.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
