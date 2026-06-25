import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.environ.get("OPENAI_MODEL", "gpt-4.1")
FRONTEND_URL   = os.environ.get("FRONTEND_URL", "http://localhost:5173")

# Postgres via psycopg2 (mesma conexão do app Streamlit)
DB_HOST     = os.environ.get("DB_HOST", "")
DB_NAME     = os.environ.get("DB_NAME", "postgres")
DB_USER     = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_PORT     = int(os.environ.get("DB_PORT", "5432"))

COPERNICUS_API_KEY = os.environ.get("COPERNICUS_API_KEY", "")
COPERNICUS_URL     = "https://cds.climate.copernicus.eu/api"

VECTOR_STORE_ID_ISOMETRIC     = os.environ.get("VECTOR_STORE_ID_ISOMETRIC", "")
VECTOR_STORE_ID_NOVA_ESPERANCA = os.environ.get("VECTOR_STORE_ID_NOVA_ESPERANCA", "")
VECTOR_STORE_ID_VERRA_VCS     = os.environ.get("VECTOR_STORE_ID_VERRA_VCS", "")
VECTOR_STORE_ID_PURO_EARTH    = os.environ.get("VECTOR_STORE_ID_PURO_EARTH", "")
VECTOR_STORE_ID_RAINBOW       = os.environ.get("VECTOR_STORE_ID_RAINBOW", "")
VECTOR_STORE_ID_C_SINK        = os.environ.get("VECTOR_STORE_ID_C_SINK", "")

METHODOLOGY_REGISTRY = {
    "isometric": {
        "label": "Isometric Biochar",
        "version": "v1.5.1",
        "vector_store_id": VECTOR_STORE_ID_ISOMETRIC,
        "requirements_module": "methodology_requirements.isometric_biochar_v1",
    },
    "verra_vcs": {
        "label": "Verra VCS",
        "version": "v4",
        "vector_store_id": VECTOR_STORE_ID_VERRA_VCS,
        "requirements_module": None,
    },
    "puro_earth": {
        "label": "Puro.Earth Biochar",
        "version": "Edition 2025",
        "vector_store_id": VECTOR_STORE_ID_PURO_EARTH,
        "requirements_module": "methodology_requirements.puro_biochar_v2025",
    },
    "rainbow": {
        "label": "Rainbow Carbon",
        "version": "v1",
        "vector_store_id": VECTOR_STORE_ID_RAINBOW,
        "requirements_module": None,
    },
    "c_sink": {
        "label": "Global C-SINK / CSI-EBI",
        "version": "v1",
        "vector_store_id": VECTOR_STORE_ID_C_SINK,
        "requirements_module": None,
    },
}
