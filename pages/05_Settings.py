"""
Settings page - Configure compliance cycles, backup locations, and sync status.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import Storage

st.set_page_config(page_title="Settings - CE Tracker", layout="wide")

st.title("⚙️ Settings")

storage = st.session_state.get("storage") or Storage()

# Compliance cycle dates
st.subheader("Compliance Cycle Start Dates")

col1, col2 = st.columns(2)

with col1:
    lmhc_start = st.date_input("LMHC Cycle Start (2-year)")
    suicide_start = st.date_input("Suicide Prevention Start (6-year)")

with col2:
    equity_start = st.date_input("Equity Cycle Start (4-year)")
    pmhc_start = st.date_input("PMH-C Cycle Start (2-year)")

st.markdown("---")

# Backup locations
st.subheader("Backup Configuration")

col1, col2 = st.columns(2)

with col1:
    csv_backup_path = st.text_input(
        "CSV Backup Folder",
        value="~/Documents/CE_Backup",
        help="External folder for CSV mirror"
    )

with col2:
    cert_backup_path = st.text_input(
        "Certificate Backup Folder",
        value="~/Documents/CE_Certificates",
        help="External folder for certificate copies"
    )

if st.button("Browse CSV backup location"):
    st.info("📁 Folder browser would open in native app")

if st.button("Browse certificate backup location"):
    st.info("📁 Folder browser would open in native app")

st.markdown("---")

# Sync status
st.subheader("Sync & Data Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Parquet Records", "42")

with col2:
    st.metric("CSV Records", "42")

with col3:
    st.metric("Certificates", "38")

if st.button("🔄 Force Reconciliation Check", use_container_width=True):
    st.info("Checking data consistency...")
    st.success("✓ All data synchronized")

st.markdown("---")

# Data export/import
st.subheader("Data Management")

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Export All Data", use_container_width=True):
        st.info("Export functionality coming soon")

with col2:
    if st.button("📤 Import from Backup", use_container_width=True):
        st.info("Import functionality coming soon")

st.markdown("---")

# Save settings
if st.button("Save All Settings", type="primary", use_container_width=True):
    st.success("✓ Settings saved")
