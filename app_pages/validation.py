import streamlit as st


def render():
    """
    Wrapper temporário da página Validation.
    Nesta fase, a lógica legada ainda vive em aia_web.py.
    O roteador principal injeta o renderer antigo em session_state.
    """

    legacy_renderer = st.session_state.get("_validation_legacy_renderer")

    if callable(legacy_renderer):
        legacy_renderer()
        return

    st.title("Validation")
    st.caption("Methodology-based compliance review and validation readiness.")
    st.info("Legacy validation workflow not available yet.")
