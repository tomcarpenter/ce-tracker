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

# Ensure data initialized
storage.initialize()

# Load data
ce_data = storage.load_parquet()

if ce_data.empty:
    st.info("No CE records found. Add entries through the Submission page.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Go to Submission", use_container_width=True):
            st.switch_page("pages/02_Submission.py")
else:
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = sorted(ce_data["category"].unique().tolist())
        selected_category = st.multiselect(
            "Category",
            options=categories,
            default=None
        )
    
    with col2:
        # Convert to datetime if needed
        ce_data_with_dates = ce_data.copy()
        ce_data_with_dates["date"] = pd.to_datetime(ce_data_with_dates["date"])
        date_range = st.date_input(
            "Date Range",
            value=(ce_data_with_dates["date"].min().date(), ce_data_with_dates["date"].max().date()),
            help="Filter records by date"
        )
    
    with col3:
        search_text = st.text_input("Search title", placeholder="Type to filter...")
    
    # Apply filters
    import pandas as pd
    filtered = ce_data.copy()
    filtered["date"] = pd.to_datetime(filtered["date"])
    
    if selected_category:
        filtered = filtered[filtered["category"].isin(selected_category)]
    
    if len(date_range) == 2 and date_range[0] and date_range[1]:
        import datetime
        date_min = pd.Timestamp(date_range[0])
        date_max = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
        filtered = filtered[(filtered["date"] >= date_min) & (filtered["date"] < date_max)]
    
    if search_text:
        filtered = filtered[filtered["title"].str.contains(search_text, case=False, na=False)]
    
    # Display table
    st.markdown("---")
    st.subheader(f"Records: {len(filtered)}")
    
    if not filtered.empty:
        display_df = filtered[["date", "title", "category", "hours"]].copy()
        display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%Y-%m-%d")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No records match the selected filters.")
    
    # Actions
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export to CSV", use_container_width=True):
            csv = filtered.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="ce_records.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
