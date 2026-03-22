import streamlit as st


def render():
    legacy_renderer = st.session_state.get("_validation_legacy_renderer")

    if callable(legacy_renderer):
        legacy_renderer()
        return
import streamlit as st


def render_downloads_and_history(
    run_id,
    full_audit_pdf,
    eligibility_pdf,
    matrix_pdf,
    json_bytes,
    trails,
    lang,
    history,
):
    pass
    st.title("Validation")
    st.caption("Methodology-based compliance review and validation readiness.")
    st.warning("Legacy validation workflow not available.")
