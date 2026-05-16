"""
Submission page - Create new CE entry with file upload and metadata.
"""

import streamlit as st
from pathlib import Path
import sys
import uuid
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage
from utils.compliance import ComplianceTracker
from utils.hashing import compute_bytes_hash
from utils.file_manager import CertificateManager

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
        # Validate
        validation_ok, validation_msg = tracker.validate_entry({
            "title": title,
            "date": date,
            "hours": hours,
            "category": category
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
                        cert_path = f"certificates/root/{cert_uuid}"
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
                "category": category,
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
                st.session_state.clear()  # Reset form
            else:
                st.error("Failed to save entry. Check audit log.")

st.markdown("---")
st.info("""
**Tips:**
- Upload certificate immediately after course completion
- Include receipt if certificate lacks date (especially for PMH-C)
- Dates must be within compliance cycle (today back to cycle start)
""")
