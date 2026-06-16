"""
Edit Entry page - Modify existing CE records.
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import base64
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.compliance import ComplianceTracker
from utils.navigation import render_sidebar_nav
from utils.hashing import compute_bytes_hash
from utils.app_config import configured_storage

render_sidebar_nav("Edit Entry")
st.title("✏️ Edit CE Entry")

storage = st.session_state.get("storage") or configured_storage()
tracker = st.session_state.get("tracker") or ComplianceTracker(storage)

CATEGORY_OPTIONS = [
    ("is_lmhc_general", "LMHC General"),
    ("is_ethics", "Ethics"),
    ("is_roles", "Roles"),
    ("is_suicide", "Suicide Prevention"),
    ("is_equity", "Equity"),
    ("is_pmhc", "PMH-C"),
]


def certificate_file_path(certificate_path: str) -> Path | None:
    """Resolve a stored certificate path to a readable local file."""
    return storage.resolve_certificate_path(certificate_path)


def render_certificate_preview(path: Path) -> None:
    """Render a lightweight preview for the current certificate."""
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
    record_ids = ce_data_copy["id"].tolist()
    label_by_id = dict(zip(ce_data_copy["id"], ce_data_copy["label"]))
    preselected_id = st.session_state.get("edit_record_id")
    selected_index = record_ids.index(preselected_id) if preselected_id in record_ids else None
    
    selected_id = st.selectbox(
        "Select entry to edit",
        options=record_ids,
        index=selected_index,
        format_func=lambda record_id: label_by_id.get(record_id, record_id),
        placeholder="Choose an entry..."
    )
    
    if selected_id:
        # Find the selected entry
        idx = ce_data_copy[ce_data_copy["id"] == selected_id].index[0]
        entry = ce_data.loc[idx].to_dict()
        st.session_state.edit_record_id = selected_id
        
        st.markdown("---")
        
        # Display current metadata
        with st.expander("Current metadata", expanded=False):
            st.write(f"**ID:** {entry.get('id', 'N/A')}")
            st.write(f"**Created:** {entry.get('created_at', 'N/A')}")
            st.write(f"**Updated:** {entry.get('updated_at', 'N/A')}")

        current_certificate = certificate_file_path(entry.get("certificate_path", ""))
        st.markdown("---")
        st.subheader("Certificate")

        if current_certificate:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(current_certificate.name)
            with col2:
                st.download_button(
                    "Download File",
                    data=current_certificate.read_bytes(),
                    file_name=current_certificate.name,
                    mime="application/octet-stream",
                    use_container_width=True,
                )

            with st.expander("View Current File"):
                render_certificate_preview(current_certificate)
        else:
            st.info("No certificate attached.")
        
        with st.form("ce_edit_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date Completed", value=pd.to_datetime(entry.get("date")))
                title = st.text_input("Course/Training Title", value=entry.get("title", ""))
            
            with col2:
                hours = st.number_input(
                    "CE Hours",
                    min_value=0.0,
                    max_value=40.0,
                    step=0.5,
                    value=float(entry.get("hours", 0))
                )

            trainer_name = st.text_input(
                "Trainer Name",
                value=entry.get("trainer_name", ""),
            )
            organization = st.text_input(
                "Organization",
                value=entry.get("organization", ""),
            )

            st.markdown("---")
            st.subheader("Compliance Categories")
            selected_categories = {}
            col1, col2, col3 = st.columns(3)
            category_columns = [col1, col2, col3, col1, col2, col3]
            for column, (flag, label) in zip(category_columns, CATEGORY_OPTIONS):
                with column:
                    selected_categories[flag] = st.checkbox(
                        label,
                        value=bool(entry.get(flag, 0)),
                    )
            
            notes = st.text_area(
                "Additional Notes",
                height=100,
                value=entry.get("notes", "")
            )

            st.markdown("---")
            st.subheader("Manage Certificate")
            replacement_certificate = st.file_uploader(
                "Add or replace certificate",
                type=["pdf", "png", "jpg", "jpeg"],
            )
            remove_certificate = st.checkbox(
                "Remove current certificate",
                disabled=not bool(entry.get("certificate_path", "")),
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                submitted = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
            
            with col2:
                st.write("")
            
            with col3:
                deleted = st.form_submit_button("🗑️ Delete Entry", type="secondary", use_container_width=True)
            
            if submitted:
                validation_ok, validation_msg = tracker.validate_entry({
                    "title": title,
                    "date": date,
                    "hours": hours,
                    **selected_categories,
                })

                if not validation_ok:
                    st.error(validation_msg)
                    st.stop()

                # Update entry
                entry["date"] = date
                entry["title"] = title
                entry["trainer_name"] = trainer_name
                entry["organization"] = organization
                entry.update({flag: int(selected) for flag, selected in selected_categories.items()})
                entry["hours"] = hours
                entry["notes"] = notes
                entry["updated_at"] = datetime.now().isoformat()

                cert_mgr = storage.certificate_manager()

                if replacement_certificate:
                    file_data = replacement_certificate.read()
                    file_hash = compute_bytes_hash(file_data)
                    cert_uuid = cert_mgr.store_certificate(
                        file_data=file_data,
                        original_filename=replacement_certificate.name,
                        file_hash=file_hash,
                        record_id=entry["id"],
                    )

                    if cert_uuid:
                        cert_mgr.delete_certificate_by_path(entry.get("certificate_path", ""))
                        entry["certificate_path"] = (
                            str(storage.certificate_root_dir / f"{cert_uuid}{Path(replacement_certificate.name).suffix}")
                        )
                        entry["certificate_hash"] = file_hash
                    else:
                        st.error("Failed to store replacement certificate")
                        st.stop()
                elif remove_certificate:
                    cert_mgr.delete_certificate_by_path(entry.get("certificate_path", ""))
                    entry["certificate_path"] = ""
                    entry["certificate_hash"] = ""
                
                success = storage.write_record(entry)
                
                if success:
                    st.success("✓ Entry updated successfully")
                    st.rerun()
                else:
                    st.error("Failed to update entry")
            
            if deleted:
                # Delete entry
                storage.certificate_manager().delete_certificate_by_path(entry.get("certificate_path", ""))
                success = storage.delete_record(entry["id"])
                
                if success:
                    st.success("✓ Entry deleted successfully")
                    st.rerun()
                else:
                    st.error("Failed to delete entry")
