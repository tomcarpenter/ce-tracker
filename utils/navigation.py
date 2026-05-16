"""Shared sidebar navigation for the Streamlit app."""

import streamlit as st


def render_sidebar_nav(active_page: str) -> None:
    """Render app navigation without exposing Streamlit's default app.py entry."""
    pages = [
        ("Dashboard", "📊", "app.py"),
        ("Submission", "➕", "pages/02_Submission.py"),
        ("Data Viewer", "🔍", "pages/03_Data_Viewer.py"),
        ("Edit Entry", "✏️", "pages/04_Edit_Entry.py"),
        ("Settings", "⚙️", "pages/05_Settings.py"),
    ]

    with st.sidebar:
        for label, icon, target in pages:
            if st.button(
                f"{icon} {label}",
                disabled=active_page == label,
                use_container_width=True,
            ):
                st.switch_page(target)
