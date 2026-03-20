import os
from typing import Dict, Any, List

import streamlit as st


def get_config_value(name: str, default: str | None = None) -> str | None:
    try:
        if name in st.secrets:
            value = st.secrets[name]
            if value is not None and str(value).strip():
                return str(value)
    except Exception:
        pass

    value = os.getenv(name, default)
    if value is None:
        return default
    return str(value)


METHODOLOGY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "isometric": {
        "label": "ISOMETRIC",
        "vector_store_id": get_config_value("VECTOR_STORE_ID_ISOMETRIC"),
        "requirements_key": "isometric",
    },
    "verra_vcs": {
        "label": "VERRA VCS",
        "vector_store_id": get_config_value("VECTOR_STORE_ID_VERRA_VCS"),
        "requirements_key": "verra_vcs",
    },
    "puro_earth": {
        "label": "PURO.EARTH",
        "vector_store_id": get_config_value("VECTOR_STORE_ID_PURO_EARTH"),
        "requirements_key": "puro_earth",
    },
    "rainbow": {
        "label": "RAINBOW",
        "vector_store_id": get_config_value("VECTOR_STORE_ID_RAINBOW"),
        "requirements_key": "rainbow",
    },
    "c_sink": {
        "label": "GLOBAL C-SINK / CSI-EBI",
        "vector_store_id": get_config_value("VECTOR_STORE_ID_C_SINK"),
        "requirements_key": "c_sink",
    },
}


def list_methodology_keys() -> List[str]:
    return list(METHODOLOGY_REGISTRY.keys())


def get_methodology_config(methodology_key: str) -> Dict[str, Any]:
    return METHODOLOGY_REGISTRY.get((methodology_key or "").strip().lower(), {})


def get_methodology_vector_store_id(methodology_key: str) -> str | None:
    config = get_methodology_config(methodology_key)
    return config.get("vector_store_id")


# Compatibilidade temporária com código legado
METHODOLOGY_VECTOR_STORES = {
    key: value.get("vector_store_id")
    for key, value in METHODOLOGY_REGISTRY.items()
}
