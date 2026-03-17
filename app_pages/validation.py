import streamlit as st


def render():
    legacy_renderer = st.session_state.get("_validation_legacy_renderer")

    if callable(legacy_renderer):
        legacy_renderer()
        return

    st.title("Validation")
    st.caption("Methodology-based compliance review and validation readiness.")
    st.warning("Legacy validation workflow not available.")
