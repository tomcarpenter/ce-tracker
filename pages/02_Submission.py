"""
Submission page - Create new CE entry with file upload and metadata.
"""

import streamlit as st
from pathlib import Path
import sys
import uuid
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.compliance import ComplianceTracker
from utils.hashing import compute_bytes_hash
from utils.file_manager import CertificateManager
from utils.navigation import render_sidebar_nav
from utils.app_config import configured_storage

render_sidebar_nav("Submission")
st.title("➕ Submit CE Entry")

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

with st.form("ce_submission_form"):
    # Core fields
    col1, col2 = st.columns(2)
    
    with col1:
        date = st.date_input("Date Completed")
        title = st.text_input("Course/Training Title")
    
    with col2:
        hours = st.number_input("CE Hours", min_value=0.0, max_value=40.0, step=0.5)

    trainer_name = st.text_input("Trainer Name")
    organization = st.text_input("Organization")

    st.markdown("---")
    st.subheader("Compliance Categories")
    selected_categories = {}
    col1, col2, col3 = st.columns(3)
    category_columns = [col1, col2, col3, col1, col2, col3]
    for column, (flag, label) in zip(category_columns, CATEGORY_OPTIONS):
        with column:
            selected_categories[flag] = st.checkbox(label)
    
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
        # Validate
        validation_ok, validation_msg = tracker.validate_entry({
            "title": title,
            "date": date,
            "hours": hours,
            **selected_categories,
        })
        
        if not validation_ok:
            st.error(validation_msg)
        else:
            # Prepare record
            record_id = str(uuid.uuid4())
            cert_path = None
            cert_hash = None
            
            # Handle certificate upload if provided
            if certificate_file:
                try:
                    cert_mgr = CertificateManager(
                        root_dir=Path("certificates/root"),
                        backup_dir=Path("certificates/backup")
                    )
                    
                    file_data = certificate_file.read()
                    file_hash = compute_bytes_hash(file_data)
                    
                    cert_uuid = cert_mgr.store_certificate(
                        file_data=file_data,
                        original_filename=certificate_file.name,
                        file_hash=file_hash,
                        record_id=record_id
                    )
                    
                    if cert_uuid:
                        cert_path = f"certificates/root/{cert_uuid}{Path(certificate_file.name).suffix}"
                        cert_hash = file_hash
                    else:
                        st.warning("Certificate upload failed, continuing without it")
                except Exception as e:
                    st.warning(f"Certificate error: {e}")
            
            # Create record
            record = {
                "id": record_id,
                "date": date,
                "title": title,
                "trainer_name": trainer_name,
                "organization": organization,
                **{flag: int(selected) for flag, selected in selected_categories.items()},
                "hours": hours,
                "notes": notes,
                "certificate_path": cert_path or "",
                "certificate_hash": cert_hash or "",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Write to storage
            success = storage.write_record(record)
            
            if success:
                st.success(f"✓ CE entry created: {title}")
                st.balloons()
            else:
                st.error("Failed to save entry. Check audit log.")

st.markdown("---")
st.info("""
**Tips:**
- Upload certificate immediately after course completion
- Include receipt if certificate lacks date (especially for PMH-C)
- Dates must be within compliance cycle (today back to cycle start)
""")
