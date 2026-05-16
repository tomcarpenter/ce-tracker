"""
Data Viewer page - Browse, filter, and inspect CE records.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.navigation import render_sidebar_nav
from utils.storage import CATEGORY_LABELS
from utils.ce_export import attachment_filename, build_ce_zip, has_attachment

render_sidebar_nav("Data Viewer")
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
        selected_category = st.multiselect(
            "Category",
            options=list(CATEGORY_LABELS.values()),
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
    filtered = ce_data.copy()
    filtered["date"] = pd.to_datetime(filtered["date"])
    
    if selected_category:
        selected_flags = [
            flag for flag, label in CATEGORY_LABELS.items() if label in selected_category
        ]
        matches_selected_category = pd.Series(False, index=filtered.index)
        for flag in selected_flags:
            if flag in filtered.columns:
                matches_selected_category = matches_selected_category | filtered[flag].fillna(0).astype(bool)
        filtered = filtered[matches_selected_category]
    
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
        display_df = filtered[["id", "date", "title", "category", "hours", "certificate_path"]].copy()
        display_df.insert(0, "selected", False)
        display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%Y-%m-%d")
        display_df["has_attachments"] = display_df["certificate_path"].apply(
            lambda value: "✅" if has_attachment(value) else "❌"
        )
        display_df["file_names"] = display_df["certificate_path"].apply(attachment_filename)
        display_df = display_df[
            ["selected", "id", "date", "title", "category", "hours", "has_attachments", "file_names"]
        ]

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            disabled=["date", "title", "category", "hours", "has_attachments", "file_names"],
            column_config={
                "selected": st.column_config.CheckboxColumn("Select"),
                "id": None,
                "date": "Date",
                "title": "Title",
                "category": "Categories",
                "hours": "Hours",
                "has_attachments": st.column_config.TextColumn(
                    "Has Attachments",
                    width="small",
                ),
                "file_names": st.column_config.TextColumn(
                    "Files",
                    width="medium",
                ),
            },
            key="record_selection_table",
        )

        selected_ids = edited_df.loc[edited_df["selected"], "id"].tolist()
        if len(selected_ids) > 1:
            st.warning("Select one row at a time before editing or deleting.")
    else:
        selected_ids = []
        st.info("No records match the selected filters.")

    if st.session_state.get("pending_delete_id"):
        pending_id = st.session_state.pending_delete_id
        pending_match = ce_data[ce_data["id"] == pending_id]
        pending_title = (
            pending_match.iloc[0].get("title", "selected entry")
            if not pending_match.empty
            else "selected entry"
        )

        st.warning(f"Confirm deletion of: {pending_title}")
        confirm_delete = st.checkbox("Yes, permanently delete this CE entry")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Confirm Delete", type="primary", disabled=not confirm_delete, use_container_width=True):
                if storage.delete_record(pending_id):
                    st.session_state.pop("pending_delete_id", None)
                    st.success("Entry deleted")
                    st.rerun()
                else:
                    st.error("Failed to delete entry")

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.pop("pending_delete_id", None)
                st.rerun()

    # Actions
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("✏️ Edit Selected", disabled=len(selected_ids) != 1, use_container_width=True):
            st.session_state.edit_record_id = selected_ids[0]
            st.switch_page("pages/04_Edit_Entry.py")

    with col2:
        if st.button("🗑️ Delete Selected", disabled=len(selected_ids) != 1, use_container_width=True):
            st.session_state.pending_delete_id = selected_ids[0]
            st.rerun()

    with col3:
        selected_records = filtered[filtered["id"].isin(selected_ids)] if selected_ids else pd.DataFrame()
        zip_data, record_count, file_count = build_ce_zip(selected_records) if selected_ids else (b"", 0, 0)
        st.download_button(
            "📎 Download CE Packet",
            data=zip_data,
            file_name="ce_export.zip",
            mime="application/zip",
            disabled=record_count == 0,
            use_container_width=True,
        )
        if selected_ids and file_count == 0:
            st.caption("Packet will include details text; no attached files found.")

    with col4:
        if st.button("📄 Export to CSV", use_container_width=True):
            csv = filtered.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="ce_records.csv",
                mime="text/csv"
            )

    with col5:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
