"""
Data Viewer page - Browse, filter, and inspect CE records.
"""

import streamlit as st
from pathlib import Path
import sys
import base64
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.navigation import render_sidebar_nav
from utils.storage import CATEGORY_LABELS
from utils.ce_export import attachment_filename, build_ce_zip, certificate_path, has_attachment
from utils.app_config import configured_storage


def render_file_preview(path: Path) -> None:
    """Render a lightweight preview for the selected row's attachment."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        encoded_pdf = base64.b64encode(path.read_bytes()).decode("utf-8")
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{encoded_pdf}" width="100%" height="520"></iframe>',
            unsafe_allow_html=True,
        )
    elif suffix in {".png", ".jpg", ".jpeg"}:
        st.image(str(path), use_column_width=True)
    else:
        st.info("Preview is not available for this file type.")

render_sidebar_nav("Data Viewer")
st.title("🔍 Data Viewer")

storage = st.session_state.get("storage") or configured_storage()

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
        search_text = st.text_input("Search records", placeholder="Search title, trainer, or organization...")
    
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
        search_columns = ["title", "trainer_name", "organization"]
        matches_search = pd.Series(False, index=filtered.index)
        for column in search_columns:
            if column in filtered.columns:
                matches_search = matches_search | filtered[column].str.contains(
                    search_text,
                    case=False,
                    na=False,
                )
        filtered = filtered[matches_search]
    
    # Display table
    st.markdown("---")
    st.subheader(f"Records: {len(filtered)}")
    
    if not filtered.empty:
        display_df = filtered[
            [
                "id",
                "date",
                "title",
                "trainer_name",
                "organization",
                "category",
                "hours",
                "certificate_path",
            ]
        ].copy()
        display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%Y-%m-%d")
        display_df["has_attachments"] = display_df["certificate_path"].apply(
            lambda value: "✅" if has_attachment(value) else "❌"
        )
        display_df["file_names"] = display_df["certificate_path"].apply(attachment_filename)
        display_df = display_df[
            [
                "id",
                "date",
                "title",
                "trainer_name",
                "organization",
                "category",
                "hours",
                "has_attachments",
                "file_names",
            ]
        ]

        selection = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "id": None,
                "date": "Date",
                "title": "Title",
                "trainer_name": "Trainer",
                "organization": "Organization",
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

        selected_rows = selection.selection.rows
        selected_ids = [display_df.iloc[selected_rows[0]]["id"]] if selected_rows else []
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

    selected_records = filtered[filtered["id"].isin(selected_ids)] if selected_ids else pd.DataFrame()

    if len(selected_records) == 1:
        selected_record = selected_records.iloc[0]
        selected_file = certificate_path(selected_record)

        with st.expander("View Current File", expanded=False):
            if selected_file:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(selected_file.name)
                with col2:
                    st.download_button(
                        "Download File",
                        data=selected_file.read_bytes(),
                        file_name=selected_file.name,
                        mime="application/octet-stream",
                        use_container_width=True,
                    )

                render_file_preview(selected_file)
            else:
                st.info("No attachment is available for the selected row.")

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
