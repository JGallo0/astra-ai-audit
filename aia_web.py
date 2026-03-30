import io
import json
import os
import time
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from project_config import (
    METHODOLOGY_REGISTRY,
    METHODOLOGY_VECTOR_STORES,
    list_methodology_keys,
    get_methodology_config,
    get_methodology_vector_store_id,
)
from scoring import calculate_compliance_score, classify_compliance_score
from project_service import (
    create_project_record,
    list_projects_by_owner,
    save_chat_message,
    load_chat_history,
    save_audit_output,
    list_audit_outputs,
)
from dotenv import load_dotenv
from openai import OpenAI
from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


from smart_search import normalize_sources, rank_sources, build_smart_context
from audit_engine import AuditEngine
from methodology_requirements import get_requirements_for_methodology
from ui_config import APP_NAME, APP_SUBTITLE, APP_TAGLINE, LOGO_DEFAULT_PATH, THEME, I18N, t
from app_pages import (
    dashboard,
    all_projects,
    create_project,
    pre_feasibility,
    full_feasibility,
    verification,
    data_room,
    document_filler,
    spreadsheet_filler,
    methodology_library,
    settings_page,
    audit_history_page,
    user_access_page,
)
from app_pages.validation_utils import (
    build_audit_dataframe,
    convert_df_to_csv_bytes,
    convert_json_to_bytes,
    docx_from_text,
    pdf_from_text,
    matrix_to_docx_bytes,
    matrix_to_pdf_bytes,
    build_full_audit_text,
    build_full_eligibility_dossier_text,
    render_sources_block,
    badge_html,
    status_badge,
    risk_badge,
)
from schemas.project_schema import get_demo_project_data
from versioning.methodology_manager import get_requirements
from engine.requirement_logic import run_engine


from app_pages.audit_runner import (
    execute_full_audit,
    execute_rerun_failures,

)
def safe_str(value):
    if value is None:
        return ""
    return str(value)


def sanitize_xml_text(value):
    if value is None:
        return ""
    text = str(value)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


try:
    from db import execute as db_execute, fetch as db_fetch, fetch_one as db_fetch_one
    DB_MODULE_AVAILABLE = True
    DB_CONNECTION_OK = False
    DB_CONNECTION_ERROR = ""

    try:
        _db_test = db_fetch_one("SELECT 1 AS ok")
        if _db_test and str(_db_test.get("ok")) == "1":
            DB_CONNECTION_OK = True
        else:
            DB_CONNECTION_ERROR = "Teste SELECT 1 não retornou resultado esperado."
    except Exception as _e:
        DB_CONNECTION_OK = False
        DB_CONNECTION_ERROR = str(_e)

except Exception as e:
    db_execute = None
    db_fetch = None
    db_fetch_one = None
    DB_MODULE_AVAILABLE = False
    DB_CONNECTION_OK = False
    DB_CONNECTION_ERROR = str(e)


# =========================================================
# CONFIG
# =========================================================

load_dotenv()


def get_config_value(name: str, default: Optional[str] = None) -> Optional[str]:
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


def get_bool_config(name: str, default: bool = False) -> bool:
    value = get_config_value(name, str(default).lower())
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def get_int_config(name: str, default: int) -> int:
    try:
        return int(get_config_value(name, str(default)))
    except Exception:
        return default


def get_list_config(name: str, default: Optional[List[str]] = None) -> List[str]:
    default = default or []

    try:
        if name in st.secrets:
            value = st.secrets[name]
            if isinstance(value, list):
                return [str(x).strip().lower() for x in value if str(x).strip()]
            if isinstance(value, str):
                return [x.strip().lower() for x in value.split(",") if x.strip()]
    except Exception:
        pass

    raw = os.getenv(name)
    if raw:
        return [x.strip().lower() for x in raw.split(",") if x.strip()]

    return [str(x).strip().lower() for x in default if str(x).strip()]


# =========================================================
# OPENAI
# =========================================================

OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada em st.secrets nem no .env")

MODEL_NAME = get_config_value("OPENAI_MODEL", "gpt-4o-mini")

PROJECT_MAX_RESULTS = get_int_config("PROJECT_MAX_RESULTS", 5)
METHODOLOGY_MAX_RESULTS = get_int_config("METHODOLOGY_MAX_RESULTS", 5)

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================================================
# OPENAI VECTOR STORE HELPERS
# =========================================================

def wait_for_vector_store_file(
    vector_store_id: str,
    vector_store_file_id: str,
    timeout_seconds: int = 180,
    poll_interval_seconds: int = 2,
):
    start = time.time()

    while time.time() - start < timeout_seconds:
        vs_file = client.vector_stores.files.retrieve(
            vector_store_id=vector_store_id,
            file_id=vector_store_file_id,
        )

        status = getattr(vs_file, "status", None)

        if status == "completed":
            return vs_file

        if status in {"failed", "cancelled"}:
            last_error = getattr(vs_file, "last_error", None)
            error_message = ""
            if last_error:
                error_message = f" | detalhe: {last_error}"
            raise RuntimeError(
                f"Falha ao indexar arquivo no vector store. status={status}{error_message}"
            )

        time.sleep(poll_interval_seconds)

    raise TimeoutError("Tempo excedido aguardando indexação dos arquivos no vector store.")


def create_project_vector_store_from_uploads(
    project_name: str,
    uploaded_files: List[Any],
) -> str:
    if not uploaded_files:
        raise ValueError("Nenhum arquivo foi enviado para criação do vector store.")

    vector_store = client.vector_stores.create(
        name=f"project_{(project_name or 'sem_nome').strip()}"
    )

    vector_store_id = vector_store.id

    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.getvalue()
        file_buffer = io.BytesIO(file_bytes)
        file_buffer.name = uploaded_file.name

        created_file = client.files.create(
            file=file_buffer,
            purpose="assistants",
        )

        attached = client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=created_file.id,
        )

        wait_for_vector_store_file(
            vector_store_id=vector_store_id,
            vector_store_file_id=attached.id,
        )

    return vector_store_id

# =========================================================
# VECTOR STORES
# =========================================================

VECTOR_STORE_ID_ISOMETRIC = get_config_value("VECTOR_STORE_ID_ISOMETRIC")
VECTOR_STORE_ID_NOVA_ESPERANCA = get_config_value("VECTOR_STORE_ID_NOVA_ESPERANCA")

vector_store_ids = [
    vs for vs in [
        VECTOR_STORE_ID_ISOMETRIC,
        VECTOR_STORE_ID_NOVA_ESPERANCA
    ] if vs
]

tools = []
if vector_store_ids:
    tools = [
        {
            "type": "file_search",
            "vector_store_ids": vector_store_ids
        }
    ]


# =========================================================
# LIMITES DE USO (ESSENCIAL – estava faltando)
# =========================================================

ADMIN_CHAT_LIMIT = get_int_config("ADMIN_CHAT_LIMIT", 9999)
ADMIN_FULL_AUDIT_LIMIT = get_int_config("ADMIN_FULL_AUDIT_LIMIT", 9999)

INTERNAL_CHAT_LIMIT = get_int_config("INTERNAL_CHAT_LIMIT", 500)
INTERNAL_FULL_AUDIT_LIMIT = get_int_config("INTERNAL_FULL_AUDIT_LIMIT", 50)

PILOT_CHAT_LIMIT = get_int_config("PILOT_CHAT_LIMIT", 50)
PILOT_FULL_AUDIT_LIMIT = get_int_config("PILOT_FULL_AUDIT_LIMIT", 5)

PROJECT_MAX_RESULTS = get_int_config("PROJECT_MAX_RESULTS", 10)
METHODOLOGY_MAX_RESULTS = get_int_config("METHODOLOGY_MAX_RESULTS", 10)


# =========================================================
# PROMPTS DO SISTEMA
# =========================================================

BASE_SYSTEM_PROMPT = """
Você é a AuditorIA, uma auditora técnica especializada em projetos de carbono, com foco em remoção via biochar.

Princípios obrigatórios:
- Use apenas o conteúdo documental recuperado da base.
- Não invente fatos.
- Não complete lacunas com suposições.
- Não use conhecimento externo quando a resposta depender de evidência documental.
- Quando houver evidência insuficiente, diga isso explicitamente.
- Quando houver conflito entre documentos, sinalize o conflito claramente.
"""

CHAT_SYSTEM_PROMPT = """
Você é a AuditorIA, assistente técnico-documental de projetos de carbono.

Sua função é responder perguntas com base EXCLUSIVAMENTE nas evidências recuperadas da base documental.

Regras obrigatórias:
- Use somente os trechos recuperados.
- Não use conhecimento externo.
- Não invente dados ausentes.
- Diferencie claramente:
  1. evidência encontrada
  2. ausência documental
  3. inconsistência documental
  4. potencial não conformidade
- Quando a pergunta envolver conformidade, compare explicitamente Projeto × Metodologia.

Formato preferencial da resposta:
1. Resposta objetiva
2. Evidências encontradas
3. Lacunas ou inconsistências
4. Recomendação prática
5. Nível de risco
"""

AUDIT_REASONING_PROMPT = """
Você é um auditor técnico especializado em projetos de remoção de carbono via biochar.

Objetivo:
Avaliar conformidade documental entre o projeto e a metodologia aplicável, usando EXCLUSIVAMENTE as evidências fornecidas.

Regras obrigatórias:
- Não use conhecimento externo.
- Não invente fatos.
- Não assuma conformidade sem evidência documental.
- Compare explicitamente evidência do projeto versus requisito metodológico.
- Quando não houver evidência suficiente, diga claramente 'evidência insuficiente'.
- Diferencie:
  - ausência documental
  - inconsistência documental
  - potencial não conformidade
  - conformidade parcial
  - conformidade robusta

Estilo de resposta:
- técnico
- direto
- auditável
- sem floreios
- sem elogios
- sem linguagem vaga

Estrutura obrigatória:
1. Conclusão objetiva
2. Evidências do projeto
3. Requisitos metodológicos relevantes
4. Gap / lacuna
5. Risco
6. Recomendação prática

Classificação de risco:
- Baixo: evidência robusta e coerente
- Médio: evidência parcial, incompleta ou pouco específica
- Alto: ausência crítica, inconsistência relevante ou indício de não conformidade
"""

# =========================================================
# PAGE
# =========================================================

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌱",
    layout="wide"
)

if "language" not in st.session_state:
    st.session_state["language"] = "pt"

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "usage_counters" not in st.session_state:
    st.session_state["usage_counters"] = {}

if "current_project_id" not in st.session_state:
    st.session_state["current_project_id"] = None

if "current_project_name" not in st.session_state:
    st.session_state["current_project_name"] = None

if "current_methodology" not in st.session_state:
    st.session_state["current_methodology"] = None

if "current_project_vector_store_id" not in st.session_state:
    st.session_state["current_project_vector_store_id"] = None

if "current_methodology_vector_store_id" not in st.session_state:
    st.session_state["current_methodology_vector_store_id"] = None

if "db_status_message" not in st.session_state:
    st.session_state["db_status_message"] = ""

if "progress_state" not in st.session_state:
    st.session_state["progress_state"] = {
        "percent": 0,
        "message": "",
        "module": "",
        "stage": "",
        "execution_estimated_cost": 0.0,
        "session_estimated_cost": 0.0,
    }

if "audit_history" not in st.session_state:
    st.session_state["audit_history"] = []

if "audit_session_cost_estimate" not in st.session_state:
    st.session_state["audit_session_cost_estimate"] = 0.0

if "current_filters" not in st.session_state:
    st.session_state["current_filters"] = {
        "module": [],
        "status": [],
        "risk": [],
    }

if "structured_selected_modules" not in st.session_state:
    st.session_state["structured_selected_modules"] = []

# =========================================================
# THEME / VISUAL
# =========================================================

def inject_custom_css():
    css = f"""
    <style>

    /* FILE UPLOADER */
    [data-testid="stFileUploader"] {{
        background: #FFFFFF !important;
        border: 1px solid #D8E3DD !important;
        border-radius: 14px !important;
        padding: 0.75rem !important;
    }}

    [data-testid="stFileUploader"] * {{
        color: #1E293B !important;
    }}

    [data-testid="stFileUploaderDropzone"] {{
        background: #F7FBF8 !important;
        border: 2px dashed #D8E3DD !important;
        border-radius: 12px !important;
    }}

    [data-testid="stFileUploaderDropzone"] * {{
        color: #1E293B !important;
    }}

    [data-testid="stFileUploaderFileName"] {{
        color: #1A4D4E !important;
        font-weight: 600 !important;
    }}

    :root {{
        --primary: {THEME["primary"]};
        --secondary: {THEME["secondary"]};
        --accent: {THEME["accent"]};
        --danger: {THEME["danger"]};
        --warning: {THEME["warning"]};
        --success: {THEME["success"]};
        --background: #EEF4F1;
        --card: #FFFFFF;
        --text: #1E293B;
        --text-secondary: #5B6B7A;
        --border: #D8E3DD;
        --hover: {THEME["hover"]};
        --info: {THEME["info"]};
        --progress: {THEME["progress"]};
        --font-primary: {THEME["font_primary"]};
    }}

    html, body, [class*="css"] {{
        font-family: var(--font-primary);
        color: var(--text);
    }}

    .stApp {{
        background: var(--background);
        color: var(--text);
    }}

    [data-testid="stAppViewContainer"] {{
        background: var(--background);
        color: var(--text);
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    section[data-testid="stSidebar"] {{
        background: #F7FBF8;
        border-right: 1px solid var(--border);
    }}

    section[data-testid="stSidebar"] * {{
        color: #1E293B !important;
    }}

    p, span, label, div, li {{
        color: #1E293B;
    }}

    h1, h2, h3, h4 {{
        color: var(--primary) !important;
    }}

    .auditoria-header {{
        display: flex;
        align-items: center;
        gap: 1rem;
        background: linear-gradient(135deg, #1A4D4E 0%, #2D6A4F 100%);
        padding: 1.2rem 1.4rem;
        border-radius: 18px;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
    }}

    .auditoria-header-text h1 {{
        margin: 0;
        font-size: 2rem;
        line-height: 1.1;
        color: white !important;
    }}

    .auditoria-header-text p {{
        margin: 0.25rem 0 0 0;
        color: rgba(255,255,255,0.92) !important;
        font-size: 0.98rem;
    }}

    .auditoria-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
        margin-bottom: 0.75rem;
        color: var(--text) !important;
    }}

    .auditoria-card * {{
        color: #1E293B !important;
    }}

    .auditoria-small {{
        color: var(--text-secondary) !important;
        font-size: 0.88rem;
    }}

    .auditoria-badge {{
        display: inline-block;
        padding: 0.22rem 0.6rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-right: 0.35rem;
        margin-bottom: 0.2rem;
    }}

    .badge-success {{
        background: rgba(45,106,79,0.12);
        color: #2D6A4F !important;
    }}

    .badge-warning {{
        background: rgba(249,199,79,0.22);
        color: #8A5A00 !important;
    }}

    .badge-danger {{
        background: rgba(217,4,41,0.12);
        color: #D90429 !important;
    }}

    .badge-info {{
        background: rgba(59,130,246,0.12);
        color: #3B82F6 !important;
    }}

    div[data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 0.8rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
    }}

    div[data-testid="stMetric"] * {{
        color: #1E293B !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: #1A4D4E !important;
        font-weight: 700 !important;
    }}

    div.stButton > button {{
        border-radius: 12px;
        border: 1px solid var(--primary);
        background: var(--primary);
        color: white !important;
        font-weight: 600;
    }}

    div.stButton > button:hover {{
        background: var(--hover);
        color: #1E293B !important;
        border-color: var(--hover);
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: #FFFFFF;
        border-radius: 12px 12px 0 0;
        border: 1px solid var(--border);
        color: #1E293B !important;
        padding: 0.5rem 0.9rem;
    }}

    .stTabs [aria-selected="true"] {{
        background: #E8F3EC !important;
        color: #1A4D4E !important;
    }}

    .stSelectbox label,
    .stMultiSelect label,
    .stTextInput label,
    .stTextArea label,
    .stRadio label,
    .stCheckbox label {{
        color: #1E293B !important;
        font-weight: 600;
    }}

    input, textarea {{
        color: #1E293B !important;
    }}

    [data-baseweb="select"] * {{
        color: #1E293B !important;
    }}

    .stDataFrame, .stTable {{
        background: #FFFFFF;
        color: #1E293B !important;
    }}

    [data-testid="stChatInput"] * {{
        color: #1E293B !important;
    }}

    [data-baseweb="select"] > div {{
        background: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #D8E3DD !important;
    }}

    [data-baseweb="select"] span {{
        color: #1E293B !important;
    }}

    [data-baseweb="select"] input {{
        color: #1E293B !important;
    }}

    [data-baseweb="tag"] {{
        background: #E8F3EC !important;
        color: #1A4D4E !important;
        border: 1px solid #D8E3DD !important;
    }}

    [data-baseweb="tag"] * {{
        color: #1A4D4E !important;
    }}

    .stCheckbox label,
    .stRadio label {{
        color: #1E293B !important;
    }}

    .stCheckbox div[data-testid="stMarkdownContainer"] p,
    .stRadio div[data-testid="stMarkdownContainer"] p {{
        color: #1E293B !important;
    }}

    [data-testid="stChatInput"] {{
        background: transparent !important;
    }}

    [data-testid="stChatInput"] > div {{
        background: #EEF4F1 !important;
        border-top: 1px solid #D8E3DD !important;
    }}

    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] input {{
        background: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #D8E3DD !important;
        border-radius: 12px !important;
    }}

    [data-testid="stChatInput"] button {{
        background: #1A4D4E !important;
        color: #FFFFFF !important;
        border: none !important;
    }}

    [data-testid="stChatInput"] button:hover {{
        background: #8BBD1E !important;
        color: #1E293B !important;
    }}

    [role="listbox"] {{
        background: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #D8E3DD !important;
    }}

    [role="option"] {{
        background: #FFFFFF !important;
        color: #1E293B !important;
    }}

    [role="option"]:hover {{
        background: #E8F3EC !important;
        color: #1A4D4E !important;
    }}

    [data-baseweb="popover"] {{
        background: #FFFFFF !important;
        color: #1E293B !important;
    }}

    [data-baseweb="popover"] * {{
        color: #1E293B !important;
    }}

    code {{
        background: #E8F3EC !important;
        color: #1A4D4E !important;
        border: 1px solid #D8E3DD !important;
        border-radius: 8px !important;
        padding: 0.12rem 0.35rem !important;
    }}

    .stMarkdown code {{
        background: #E8F3EC !important;
        color: #1A4D4E !important;
        border: 1px solid #D8E3DD !important;
    }}

    [data-testid="stBottomBlockContainer"] {{
        background: #EEF4F1 !important;
        border-top: 1px solid #D8E3DD !important;
    }}

    [data-testid="stChatInput"] {{
        background: #EEF4F1 !important;
    }}

    [data-testid="stChatInput"] > div {{
        background: #EEF4F1 !important;
        border-top: none !important;
    }}

    footer {{
        background: #EEF4F1 !important;
    }}

    [data-testid="stExpander"] {{
        background: #FFFFFF !important;
        border: 1px solid #D8E3DD !important;
        border-radius: 14px !important;
        overflow: hidden !important;
    }}

    [data-testid="stExpander"] details {{
        background: #FFFFFF !important;
    }}

    [data-testid="stExpander"] summary {{
        background: #F7FBF8 !important;
        color: #1A4D4E !important;
        border-bottom: 1px solid #D8E3DD !important;
    }}

    [data-testid="stExpander"] summary * {{
        color: #1A4D4E !important;
    }}

    [data-testid="stExpanderDetails"] {{
        background: #FFFFFF !important;
        color: #1E293B !important;
    }}

    [data-testid="stExpanderDetails"] * {{
        color: #1E293B !important;
    }}

    .stTextInput > div > div > input {{
        background: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #D8E3DD !important;
        border-radius: 10px !important;
    }}

    .stTextInput label {{
        color: #1E293B !important;
        font-weight: 600 !important;
    }}

    .stMultiSelect > div > div {{
        background: #FFFFFF !important;
        color: #1E293B !important;
        border-radius: 10px !important;
        border: 1px solid #D8E3DD !important;
    }}

    .stMultiSelect * {{
        color: #1E293B !important;
    }}

    [data-baseweb="tag"] {{
        background: #E8F3EC !important;
        color: #1A4D4E !important;
        border: 1px solid #D8E3DD !important;
        border-radius: 8px !important;
    }}

    [data-baseweb="tag"] * {{
        color: #1A4D4E !important;
    }}

    .stRadio > label,
    .stCheckbox > label {{
        color: #1E293B !important;
        font-weight: 600 !important;
    }}

    .stRadio div[role="radiogroup"] *,
    .stCheckbox * {{
        color: #1E293B !important;
    }}

    div[data-testid="stDownloadButton"] > button {{
        background: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #D8E3DD !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }}

    div[data-testid="stDownloadButton"] > button:hover {{
        background: #E8F3EC !important;
        color: #1A4D4E !important;
        border: 1px solid #A2D729 !important;
    }}

    div[data-testid="stDownloadButton"] > button * {{
        color: #1E293B !important;
    }}

    /* SIDEBAR BUTTONS */
    section[data-testid="stSidebar"] .stButton > button {{
        background: #0f5c5a !important;
        color: #ffffff !important;
        border: 1px solid #0f5c5a !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        min-height: 44px !important;
        white-space: nowrap !important;
    }}

    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: #14736f !important;
        color: #ffffff !important;
        border: 1px solid #14736f !important;
    }}

    /* FORM BUTTON */
    div[data-testid="stForm"] .stButton > button {{
        background: #0f5c5a !important;
        color: #ffffff !important;
        border: 1px solid #0f5c5a !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }}

    div[data-testid="stForm"] .stButton > button:hover {{
        background: #14736f !important;
        color: #ffffff !important;
        border: 1px solid #14736f !important;
    }}

    /* Garantir texto branco */
    section[data-testid="stSidebar"] .stButton > button *,
    div[data-testid="stForm"] .stButton > button * {{
        color: #ffffff !important;
    }}
    /* FILE UPLOADER BUTTON */
    [data-testid="stFileUploader"] button {{
        background: #0f5c5a !important;
        color: #ffffff !important;
        border: 1px solid #0f5c5a !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }}

    [data-testid="stFileUploader"] button:hover {{
        background: #14736f !important;
        color: #ffffff !important;
        border: 1px solid #14736f !important;
    }}

    [data-testid="stFileUploader"] button * {{
        color: #ffffff !important;
    }}

    /* DISABLED BUTTONS */
    section[data-testid="stSidebar"] .stButton > button:disabled,
    div[data-testid="stForm"] .stButton > button:disabled,
    [data-testid="stFileUploader"] button:disabled {{
        background: #DCE9E2 !important;
        color: #6B7C75 !important;
        border: 1px solid #C8D8D0 !important;
        opacity: 1 !important;
        cursor: not-allowed !important;
    }}

    section[data-testid="stSidebar"] .stButton > button:disabled *,
    div[data-testid="stForm"] .stButton > button:disabled *,
    [data-testid="stFileUploader"] button:disabled * {{
        color: #6B7C75 !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# =========================================================
# DB / AUTH HELPERS
# =========================================================

def db_is_configured() -> bool:
    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    for key in required:
        value = get_config_value(key)
        if not value or not str(value).strip():
            return False
    return DB_MODULE_AVAILABLE


def db_execute_safe(query: str, params=None) -> bool:
    if not db_is_configured() or db_execute is None:
        return False
    try:
        db_execute(query, params)
        return True
    except Exception as e:
        st.session_state["db_status_message"] = f"DB execute error: {str(e)}"
        return False


def db_fetch_safe(query: str, params=None) -> List[Any]:
    if not db_is_configured() or db_fetch is None:
        return []
    try:
        return db_fetch(query, params) or []
    except Exception as e:
        st.session_state["db_status_message"] = f"DB fetch error: {str(e)}"
        return []


def get_db_user_record(email: str) -> Optional[Dict[str, Any]]:
    email = safe_str(email).strip().lower()
    if not email:
        return None

    rows = db_fetch_safe(
        """
        SELECT email, name, role, status, created_at, last_login
        FROM users
        WHERE lower(email) = %s
        LIMIT 1
        """,
        (email,)
    )
    if not rows:
        return None

    row = rows[0]
    if isinstance(row, dict):
        return row

    return {
        "email": row[0] if len(row) > 0 else "",
        "name": row[1] if len(row) > 1 else "",
        "role": row[2] if len(row) > 2 else "",
        "status": row[3] if len(row) > 3 else "",
        "created_at": row[4] if len(row) > 4 else None,
        "last_login": row[5] if len(row) > 5 else None,
    }


def sync_user_to_db(user: Dict[str, str], role: str):
    email = safe_str(user.get("email", "")).strip().lower()
    name = safe_str(user.get("name", "")).strip()
    if not email:
        return

    db_execute_safe(
        """
        INSERT INTO users (email, name, role, status, last_login)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (email)
        DO UPDATE SET
            name = EXCLUDED.name,
            role = EXCLUDED.role,
            status = EXCLUDED.status,
            last_login = NOW()
        """,
        (email, name, role, "active")
    )


def ensure_project_record(owner_email: str, project_name: str):
    return
    owner_email = safe_str(owner_email).strip().lower()
    project_name = safe_str(project_name).strip()
    if not owner_email or not project_name:
        return

    existing = db_fetch_safe(
        """
        SELECT id
        FROM projects
        WHERE lower(owner_email) = %s
          AND lower(project_name) = %s
        LIMIT 1
        """,
        (owner_email, project_name.lower())
    )

    if existing:
        return

    db_execute_safe(
        """
        INSERT INTO projects (owner_email, project_name, created_at)
        VALUES (%s, %s, NOW())
        """,
        (owner_email, project_name)
    )


def auth_available() -> bool:
    return hasattr(st, "login") and hasattr(st, "logout") and hasattr(st, "user")


def get_configured_auth_providers() -> List[str]:
    providers = []

    try:
        auth_block = st.secrets["auth"]
        if "google" in auth_block:
            providers.append("google")
        if "microsoft" in auth_block:
            providers.append("microsoft")
    except Exception:
        pass

    return providers

AUTH_REQUIRED = get_bool_config("AUTH_REQUIRED", False)
ALLOW_LOCAL_BYPASS = get_bool_config("ALLOW_LOCAL_BYPASS", True)
def get_user_info() -> Dict[str, str]:
    if auth_available() and getattr(st.user, "is_logged_in", False):
        email = safe_str(getattr(st.user, "email", "")).strip().lower()
        name = safe_str(getattr(st.user, "name", "")).strip() or email or "Usuário autenticado"
        return {
            "is_logged_in": True,
            "email": email,
            "name": name,
            "auth_mode": "oidc",
        }

    if not AUTH_REQUIRED and ALLOW_LOCAL_BYPASS:
        return {
            "is_logged_in": True,
            "email": "local.dev@auditoria.local",
            "name": "Local Dev",
            "auth_mode": "local_bypass",
        }

    return {
        "is_logged_in": False,
        "email": "",
        "name": "",
        "auth_mode": "none",
    }


def email_domain(email: str) -> str:
    email = (email or "").strip().lower()
    if "@" not in email:
        return ""
    return email.split("@", 1)[1]


def is_user_allowed(email: str) -> bool:
    email = (email or "").strip().lower()
    domain = email_domain(email)

    if not email:
        return False
    if email in ADMIN_EMAILS:
        return True
    if ALLOWED_EMAILS and email in ALLOWED_EMAILS:
        return True
    if ALLOWED_DOMAINS and domain in ALLOWED_DOMAINS:
        return True
    if INTERNAL_DOMAINS and domain in INTERNAL_DOMAINS:
        return True
    if not ALLOWED_EMAILS and not ALLOWED_DOMAINS and not INTERNAL_DOMAINS and not ADMIN_EMAILS:
        return True
    return False


def get_user_role(email: str) -> str:
    email = (email or "").strip().lower()
    domain = email_domain(email)

    if not email:
        return "blocked"

    persisted = get_db_user_record(email)
    if persisted:
        persisted_status = safe_str(persisted.get("status", "active")).strip().lower()
        persisted_role = safe_str(persisted.get("role", "")).strip().lower()
        if persisted_status in {"blocked", "inactive", "disabled"}:
            return "blocked"
        if persisted_role:
            return persisted_role

    if email in ADMIN_EMAILS:
        return "admin"
    if domain in INTERNAL_DOMAINS:
        return "internal"
    if is_user_allowed(email):
        return DEFAULT_ROLE
    return "blocked"


def get_role_limits(role: str) -> Dict[str, int]:
    if role == "admin":
        return {"chat": ADMIN_CHAT_LIMIT, "full_audit": ADMIN_FULL_AUDIT_LIMIT}
    if role == "internal":
        return {"chat": INTERNAL_CHAT_LIMIT, "full_audit": INTERNAL_FULL_AUDIT_LIMIT}
    if role == "pilot_client":
        return {"chat": PILOT_CHAT_LIMIT, "full_audit": PILOT_FULL_AUDIT_LIMIT}
    return {"chat": 0, "full_audit": 0}


def get_usage_bucket_key(email: str) -> str:
    month_key = datetime.now().strftime("%Y-%m")
    return f"{email.lower()}::{month_key}"


def init_usage_bucket(email: str):
    key = get_usage_bucket_key(email)
    if key not in st.session_state["usage_counters"]:
        st.session_state["usage_counters"][key] = {"chat": 0, "full_audit": 0}


def get_usage(email: str) -> Dict[str, int]:
    init_usage_bucket(email)
    key = get_usage_bucket_key(email)
    return st.session_state["usage_counters"][key]


def can_consume(email: str, role: str, action: str) -> bool:
    limits = get_role_limits(role)
    usage = get_usage(email)
    return usage.get(action, 0) < limits.get(action, 0)


def consume_usage(email: str, action: str):
    init_usage_bucket(email)
    key = get_usage_bucket_key(email)
    st.session_state["usage_counters"][key][action] = st.session_state["usage_counters"][key].get(action, 0) + 1


def render_login_gate(lang: str):
    user = get_user_info()
    if user["is_logged_in"]:
        return user

    st.warning(t(lang, "login_required"))

    if not auth_available():
        st.error(
            "Autenticação não configurada no ambiente. "
            "Confirme se o Streamlit está com OIDC habilitado e se o arquivo "
            ".streamlit/secrets.toml contém os blocos [auth.google] e/ou [auth.microsoft]."
        )
        st.stop()

    providers = get_configured_auth_providers()

    if not providers:
        st.error(
            "Nenhum provedor de autenticação foi encontrado em st.secrets['auth']. "
            "Configure Google e/ou Microsoft no secrets.toml."
        )
        st.stop()

    st.markdown("### Entrar")

    cols = st.columns(2)

    with cols[0]:
        google_enabled = "google" in providers
        if st.button(
            "Entrar com Google",
            use_container_width=True,
            type="primary",
            disabled=not google_enabled,
            key="login_google_button",
        ):
            st.login("google")

    with cols[1]:
        microsoft_enabled = "microsoft" in providers
        if st.button(
            "Entrar com Microsoft",
            use_container_width=True,
            disabled=not microsoft_enabled,
            key="login_microsoft_button",
        ):
            st.login("microsoft")

    if not AUTH_REQUIRED and ALLOW_LOCAL_BYPASS:
        st.info("Bypass local habilitado. Em desenvolvimento, o app pode entrar sem login real.")

    st.stop()


def render_access_denied(lang: str, email: str):
    st.error(t(lang, "unauthorized"))
    st.markdown(f"**{safe_str(email)}**")
    if auth_available() and getattr(st.user, "is_logged_in", False):
        if st.button("Sair", key="logout_access_denied"):
            st.logout()
    st.stop()

def init_project_session():
    defaults = {
        "current_project_id": None,
        "current_project_name": None,
        "current_methodology": None,
        "current_project_vector_store_id": None,
        "current_methodology_vector_store_id": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_current_project(project: dict, user_email: str = "", methodology_key: str | None = None):
    methodology_key = (methodology_key or project.get("methodology") or "").strip().lower()
    methodology_config = get_methodology_config(methodology_key)

    st.session_state["current_project_id"] = project.get("id")
    st.session_state["current_project_name"] = project.get("project_name")
    st.session_state["current_project_vector_store_id"] = project.get("project_vector_store_id")

    st.session_state["current_methodology"] = methodology_key
    st.session_state["current_methodology_vector_store_id"] = methodology_config.get("vector_store_id")

    if project.get("id") and user_email:
        try:
            rows = load_chat_history(project.get("id"), user_email)
            st.session_state["messages"] = [
                {
                    "role": row.get("role", "assistant"),
                    "content": row.get("message", ""),
                }
                for row in rows
            ]
        except Exception:
            st.session_state["messages"] = []
    else:
        st.session_state["messages"] = []

def ensure_default_example_project(user_email: str):
    project_vs_id = get_config_value("VECTOR_STORE_ID_NOVA_ESPERANCA")
    methodology_vs_id = get_config_value("VECTOR_STORE_ID_ISOMETRIC")

    if not project_vs_id or not methodology_vs_id:
        return

    try:
        existing = db_fetch_safe(
            """
            SELECT id, project_name, methodology,
                   project_vector_store_id, methodology_vector_store_id
            FROM projects
            WHERE lower(owner_email) = %s
              AND lower(project_name) = %s
            LIMIT 1
            """,
            ((user_email or "").strip().lower(), "nova esperança")
        )

        if existing:
            row = existing[0]
            project_id = row.get("id")
            current_project_vs = row.get("project_vector_store_id")
            current_methodology_vs = row.get("methodology_vector_store_id")
            current_methodology = row.get("methodology")

            if (
                current_project_vs != project_vs_id
                or current_methodology_vs != methodology_vs_id
                or (current_methodology or "").strip().lower() != "isometric"
            ):
                db_execute_safe(
                    """
                    UPDATE projects
                    SET methodology = %s,
                        project_vector_store_id = %s,
                        methodology_vector_store_id = %s,
                        status = %s
                    WHERE id = %s
                    """,
                    ("isometric", project_vs_id, methodology_vs_id, "active", project_id)
                )
        else:
            create_project_record(
                project_name="Nova Esperança",
                owner_email=user_email,
                methodology="isometric",
                project_vector_store_id=project_vs_id,
                methodology_vector_store_id=methodology_vs_id,
                status="active",
            )
    except Exception as e:
        st.session_state["db_status_message"] = f"Erro ao garantir projeto exemplo: {e}"


def render_project_manager(user_email: str):
    st.sidebar.markdown("### Projetos")
    ensure_default_example_project(user_email)

    with st.sidebar.expander("➕ Criar projeto", expanded=False):
        with st.form("create_project_form", clear_on_submit=True):
            project_name = st.text_input("Nome do projeto")

            methodology = st.selectbox(
                "Metodologia inicial",
                options=list_methodology_keys(),
                format_func=lambda x: METHODOLOGY_REGISTRY[x]["label"]
            )

            st.markdown("**Documentos do projeto**")
            uploaded_files = st.file_uploader(
                "Envie os arquivos do projeto",
                accept_multiple_files=True,
                type=["pdf", "docx", "doc", "xlsx", "xls", "csv", "txt", "md", "json"],
            )

            project_vector_store_id_manual = ""

            if current_role == "admin":
                st.markdown("**Fallback técnico (admin)**")
                project_vector_store_id_manual = st.text_input(
                    "Vector Store ID do projeto (opcional)"
                )

            submitted = st.form_submit_button("Salvar projeto")

            if submitted:
                if not project_name.strip():
                    st.error("Informe o nome do projeto.")
                    st.stop()

                methodology_vector_store_id = get_methodology_vector_store_id(methodology)

                if not methodology_vector_store_id:
                    st.error("Metodologia sem vector store configurado.")
                    st.stop()

                try:
                    project_vector_store_id = None

                    if uploaded_files and len(uploaded_files) > 0:
                        with st.spinner("Criando vector store e indexando arquivos..."):
                            project_vector_store_id = create_project_vector_store_from_uploads(
                                project_name=project_name,
                                uploaded_files=uploaded_files,
                            )
                    elif project_vector_store_id_manual.strip():
                        project_vector_store_id = project_vector_store_id_manual.strip()
                    else:
                        if current_role == "admin":
                            st.error(
                                "Envie pelo menos um arquivo do projeto ou informe manualmente o Vector Store ID."
                            )
                        else:
                            st.error(
                                "Envie pelo menos um arquivo do projeto para criar o projeto."
                            )
                        st.stop()

                    create_project_record(
                        project_name=project_name,
                        owner_email=user_email,
                        methodology=methodology,
                        project_vector_store_id=project_vector_store_id,
                        methodology_vector_store_id=methodology_vector_store_id,
                    )

                    st.success("Projeto criado com sucesso.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao criar projeto: {e}")

    st.sidebar.markdown("#### Meus projetos")

    try:
        projects = [
            p for p in list_projects_by_owner(user_email)
            if p.get("project_vector_store_id")
        ]
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar projetos: {e}")
        return

    if not projects:
        st.sidebar.info("Nenhum projeto disponível ainda.")
        return

    project_options = {
        f"{p['project_name']}": p
        for p in projects
    }

    methodology_options = list_methodology_keys()

    default_project_label = None
    current_project_name = st.session_state.get("current_project_name")
    if current_project_name:
        for label, proj in project_options.items():
            if proj.get("project_name") == current_project_name:
                default_project_label = label
                break

    if default_project_label and default_project_label in list(project_options.keys()):
        default_project_index = list(project_options.keys()).index(default_project_label)
    else:
        default_project_index = 0

    current_methodology = (st.session_state.get("current_methodology") or "").strip().lower()
    if current_methodology in methodology_options:
        default_methodology_index = methodology_options.index(current_methodology)
    else:
        default_methodology_index = 0

    selected_project_label = st.sidebar.selectbox(
        "Selecionar projeto",
        options=list(project_options.keys()),
        index=default_project_index,
        key="sidebar_project_selector_v2"
    )

    selected_methodology = st.sidebar.selectbox(
        "Selecionar metodologia",
        options=methodology_options,
        index=default_methodology_index,
        format_func=lambda x: METHODOLOGY_REGISTRY[x]["label"],
        key="sidebar_methodology_selector_v2"
    )

    st.sidebar.markdown("### Seleção atual")
    st.sidebar.write(f"Projeto: {selected_project_label}")
    st.sidebar.write(
        f"Metodologia: {METHODOLOGY_REGISTRY[selected_methodology]['label']}"
    )

    if st.sidebar.button("Ativar", key="sidebar_activate_analysis_button_v2", use_container_width=True):
        set_current_project(
            project_options[selected_project_label],
            user_email,
            methodology_key=selected_methodology,
        )
        st.rerun()

# =========================================================
# AUTH GATE
# =========================================================
init_project_session()

current_user = get_user_info()
if AUTH_REQUIRED:
    current_user = render_login_gate(st.session_state["language"])

current_role = get_user_role(current_user["email"])
if current_role == "blocked":
    render_access_denied(st.session_state["language"], current_user["email"])

if db_is_configured():
    sync_user_to_db(current_user, current_role)

def render_header(lang: str):
    logo_path = "assets/auditoria_logo.png"

    try:
        import os
        if os.path.exists(logo_path):
            st.image(logo_path, width=420)
            return
    except Exception:
        pass

    app_title = APP_NAME if "APP_NAME" in globals() else "AuditorIA"

    if "APP_SUBTITLE" in globals() and isinstance(APP_SUBTITLE, dict):
        app_subtitle = APP_SUBTITLE.get(lang, APP_SUBTITLE.get("pt", "Auditoria técnica documental"))
    else:
        app_subtitle = "Auditoria técnica documental"

    st.markdown(
        f"""
        <div class="auditoria-header">
            <div class="auditoria-header-text">
                <h1>{app_title}</h1>
                <p>{app_subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
# =========================================================
# THEME LOAD
# =========================================================

inject_custom_css()
lang = st.session_state.get("language", "pt")
st.session_state["language"] = lang

# =========================================================
# HEADER
# =========================================================

render_header(lang)

# =========================================================
# AUDIT SCOPE CONFIG
# =========================================================

AUDIT_SCOPE_CONFIG = {
    "Core Integrity": {
        "label": "Core Integrity",
        "help": "Foundational methodological integrity: eligibility, ownership, additionality, baseline, and system boundary.",
        "modules": [
            "Eligibility",
            "Ownership",
            "Additionality",
            "Baseline",
            "System Boundary",
        ],
        "default": True,
    },
    "Carbon Accounting": {
        "label": "Carbon Accounting",
        "help": "Net removals logic, carbon quantification, leakage, uncertainty, and lifecycle accounting.",
        "modules": [
            "Carbon Accounting",
            "Biochar Carbon Quantification",
            "Leakage",
            "Uncertainty",
            "LCA",
        ],
        "default": True,
    },
    "MRV & Verification": {
        "label": "MRV & Verification",
        "help": "Monitoring, traceability, data integrity, and audit readiness.",
        "modules": [
            "MRV",
            "Traceability",
        ],
        "default": True,
    },
    "Durability & Storage": {
        "label": "Durability & Storage",
        "help": "Durability logic, storage integrity, reversal risk, and biochar quality.",
        "modules": [
            "Durability",
            "Storage/End Use",
            "Reversal Risk",
            "Biochar Quality",
        ],
        "default": True,
    },
    "Operations": {
        "label": "Operations",
        "help": "Operational evidence for feedstock sourcing and technology configuration.",
        "modules": [
            "Feedstock",
            "Technology",
        ],
        "default": False,
    },
    "Safeguards & Compliance": {
        "label": "Safeguards & Compliance",
        "help": "Environmental and social safeguards, permits, and legal compliance.",
        "modules": [
            "Safeguards",
            "Regulatory Compliance",
        ],
        "default": False,
    },
}


def resolve_selected_modules_from_scope(
    requirements: List[Dict[str, Any]],
    selected_scopes: List[str],
) -> List[str]:
    available_modules = {
    r.get("module")
    for r in requirements
    if isinstance(r, dict) and r.get("module")
}
    resolved_modules: List[str] = []

    for scope in selected_scopes:
        scope_config = AUDIT_SCOPE_CONFIG.get(scope, {})
        for module in scope_config.get("modules", []):
            if module in available_modules and module not in resolved_modules:
                resolved_modules.append(module)

    # base obrigatória independentemente da escolha explícita do usuário
    mandatory_modules = ["Eligibility"]

    for mandatory_module in mandatory_modules:
        if mandatory_module in available_modules and mandatory_module not in resolved_modules:
            resolved_modules.insert(0, mandatory_module)

    return resolved_modules

def get_available_audit_scopes(requirements: List[Dict[str, Any]]) -> List[str]:
    available_modules = {
        r.get("module")
        for r in requirements
        if isinstance(r, dict) and r.get("module")
    }

    available_scopes: List[str] = []

    for scope_name, scope_config in AUDIT_SCOPE_CONFIG.items():
        scope_modules = scope_config.get("modules", [])
        if any(module in available_modules for module in scope_modules):
            available_scopes.append(scope_name)

    return available_scopes


def get_default_audit_scopes(available_scopes: List[str]) -> List[str]:
    return [
        scope_name
        for scope_name in available_scopes
        if AUDIT_SCOPE_CONFIG.get(scope_name, {}).get("default", False)
    ]


def get_scope_help_text(selected_scopes: List[str]) -> str:
    parts = []
    for scope in selected_scopes:
        help_text = AUDIT_SCOPE_CONFIG.get(scope, {}).get("help")
        if help_text:
            parts.append(f"**{scope}:** {help_text}")
    return "\n\n".join(parts)
    
# =========================================================
# AUDITORIAS DISPONÍVEIS
# =========================================================

project_vs_id = st.session_state.get("current_project_vector_store_id")
methodology_vs_id = st.session_state.get("current_methodology_vector_store_id")
project_name = st.session_state.get("current_project_name")
current_methodology = st.session_state.get("current_methodology")

structured_requirements = get_requirements_for_methodology(current_methodology)

available_structured_scopes = get_available_audit_scopes(structured_requirements)
default_structured_scopes = get_default_audit_scopes(available_structured_scopes)

if "structured_selected_scopes" not in st.session_state:
    st.session_state["structured_selected_scopes"] = default_structured_scopes

if project_vs_id and methodology_vs_id and project_name and current_methodology:

    st.markdown("### Auditorias disponíveis")
    st.caption(
        "Selecione abaixo o tipo de análise a executar. "
        "O modo exploratório é assistido por IA. "
        "Os modos de auditoria estruturada usam critérios metodológicos explícitos."
    )

    structured_selected_scopes = st.multiselect(
        "Escopo da auditoria estruturada",
        options=available_structured_scopes,
        default=st.session_state.get(
            "structured_selected_scopes",
            default_structured_scopes,
        ),
        help=(
            "Core Integrity is the methodological foundation of the audit. "
            "Eligibility is always enforced internally even if scope selection changes."
        ),
        key="structured_scope_selector_v2",
    )

    structured_selected_modules = resolve_selected_modules_from_scope(
        requirements=structured_requirements,
        selected_scopes=structured_selected_scopes,
    )

    st.session_state["structured_selected_scopes"] = structured_selected_scopes
    st.session_state["structured_selected_modules"] = structured_selected_modules

    st.caption(
        "Módulos estruturados selecionados: "
        + (
            ", ".join(structured_selected_modules)
            if structured_selected_modules
            else "nenhum"
        )
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "Exploratory AI Review",
            width="stretch",
            key="run_exploratory_button",
        ):
            st.session_state["audit_mode"] = "exploratory"
            st.session_state["run_exploratory"] = True

    with c2:
        if st.button(
            "Structured Audit — Development",
            width="stretch",
            key="run_development_button",
        ):
            st.session_state["audit_mode"] = "development"
            st.session_state["run_structured"] = True

    with c3:
        if st.button(
            "Structured Audit — Operating",
            width="stretch",
            key="run_operational_button",
        ):
            st.session_state["audit_mode"] = "operational"
            st.session_state["run_structured"] = True

else:
    st.info("Selecione e ative um projeto e uma metodologia para iniciar a auditoria.")

# =========================================================
# EXECUÇÃO DA AUDITORIA ESTRUTURADA
# =========================================================

if st.session_state.get("run_structured"):

    audit_mode = st.session_state.get("audit_mode", "development")

    try:
        from engine.requirement_logic_map import REQUIREMENT_LOGIC_MAP

        requirements = get_requirements_for_methodology(current_methodology)

        # Enriquecer requirements com lógica
        for req in requirements:
            req_id = req.get("id")
            req["logic"] = REQUIREMENT_LOGIC_MAP.get(req_id)

        if not requirements:
            st.error("Nenhum requisito estruturado foi carregado.")
            st.stop()

        with st.spinner("Executando auditoria estruturada..."):

            engine = AuditEngine(
                api_key=OPENAI_API_KEY,
                model=MODEL_NAME,
                project_vector_store_id=project_vs_id,
                methodology_vector_store_id=methodology_vs_id,
                project_name=project_name,
                requirements=requirements,
            )

            selected_modules_for_v2 = st.session_state.get("structured_selected_modules") or None

            output = engine.run_structured_engine_audit(
                selected_modules=selected_modules_for_v2,
                audit_mode=audit_mode,
            )

            if not isinstance(output, dict):
                raise ValueError("Structured engine output must be a dict.")

            if "results" not in output:
                raise ValueError("Structured engine output missing 'results'.")

            if "score_data" not in output:
                raise ValueError("Structured engine output missing 'score_data'.")

            if "score_label" not in output:
                raise ValueError("Structured engine output missing 'score_label'.")

            if not isinstance(output.get("results"), list):
                st.write("DEBUG OUTPUT TYPE:", type(output))
                st.write("DEBUG OUTPUT KEYS:", list(output.keys()) if isinstance(output, dict) else "not_a_dict")
                st.write("DEBUG RESULTS TYPE:", type(output.get("results")) if isinstance(output, dict) else "no_results")
                st.write("DEBUG RESULTS VALUE:", output.get("results") if isinstance(output, dict) else "no_results")
                raise ValueError("'results' must be a list.")

            st.session_state["structured_v2_output"] = output
            st.session_state["run_structured"] = False

        st.success("Auditoria estruturada concluída com sucesso.")

    except Exception as e:
        import traceback

        st.session_state["run_structured"] = False
        st.error(f"Erro na auditoria estruturada: {e}")

        st.markdown("### DEBUG TRACEBACK")
        st.code(traceback.format_exc(), language="python")

def build_structured_audit_summary_text(
    project_name: str,
    audit_mode: str,
    score_data: Dict[str, Any],
    score_label: str,
    results: List[Dict[str, Any]],
) -> str:

    total = len(results or [])
    compliant = score_data.get("compliant", 0)
    partial = score_data.get("partial", 0)
    non_compliant = score_data.get("non_compliant", 0)
    error = score_data.get("error", 0)
    score = score_data.get("score", 0)

    # -------------------------
    # Classificação de risco
    # -------------------------
    if score >= 75:
        risk_level = "LOW"
    elif score >= 50:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    # -------------------------
    # Coleta de itens críticos
    # -------------------------
    critical = []
    partial_items = []

    for r in results or []:
        status = str(r.get("status", "")).lower()
        req_id = r.get("requirement_id", "")
        title = r.get("title", "")
        notes = r.get("notes", []) or []

        note_txt = " ".join([str(n) for n in notes]) if isinstance(notes, list) else str(notes)

        line = f"{req_id} — {title}"
        if note_txt:
            line += f" | {note_txt}"

        if status == "non_compliant":
            critical.append(line)
        elif status == "partial":
            partial_items.append(line)

    critical = critical[:5]
    partial_items = partial_items[:5]

    # -------------------------
    # Construção do texto
    # -------------------------
    lines = []

    lines.append("CO2mply | Audit Summary (Investor View)")
    lines.append("")
    lines.append(f"Project: {project_name or 'Unnamed'}")
    lines.append(f"Audit mode: {str(audit_mode).capitalize()}")
    lines.append("")

    # EXECUTIVE BLOCK
    lines.append("1. Executive Overview")
    lines.append(f"- Compliance Score: {score}")
    lines.append(f"- Rating: {score_label}")
    lines.append(f"- Risk Level: {risk_level}")
    lines.append(f"- Requirements Assessed: {total}")
    lines.append("")

    # INTERPRETAÇÃO
    lines.append("2. Strategic Interpretation")

    if risk_level == "HIGH":
        interpretation = (
            "The project currently presents a high compliance risk. "
            "Critical structural elements required by the methodology are either missing or not evidenced. "
            "In its current state, the project is not ready for validation."
        )
    elif risk_level == "MODERATE":
        interpretation = (
            "The project demonstrates partial compliance but still contains material gaps. "
            "Targeted improvements are required before proceeding to validation."
        )
    else:
        interpretation = (
            "The project demonstrates strong compliance alignment with the methodology. "
            "Remaining gaps are limited and unlikely to compromise validation."
        )

    lines.append(interpretation)
    lines.append("")

    # BREAKDOWN
    lines.append("3. Compliance Breakdown")
    lines.append(f"- Compliant: {compliant}")
    lines.append(f"- Partial: {partial}")
    lines.append(f"- Non-compliant: {non_compliant}")
    lines.append(f"- Not assessed (logic gaps): {error}")
    lines.append("")

    # PRINCIPAIS RISCOS
    lines.append("4. Key Risk Drivers")

    if critical:
        for c in critical:
            lines.append(f"- {c}")
    else:
        lines.append("- No critical non-compliance identified.")

    lines.append("")

    # ITENS PARCIAIS
    lines.append("5. Improvement Opportunities")

    if partial_items:
        for p in partial_items:
            lines.append(f"- {p}")
    else:
        lines.append("- No partial gaps identified.")

    lines.append("")

    # LIMITAÇÃO DA ENGINE
    lines.append("6. Engine Coverage Note")
    lines.append(
        "A portion of the requirements returned 'error' due to missing logic bindings. "
        "These do not necessarily indicate project non-compliance, but rather areas not yet evaluated "
        "by the deterministic engine."
    )
    lines.append("")

    # PRÓXIMOS PASSOS
    lines.append("7. Recommended Next Steps")

    if risk_level == "HIGH":
        steps = [
            "Resolve all non-compliant items before any validation attempt",
            "Define storage pathway and MRV structure",
            "Strengthen core eligibility and permanence assumptions",
        ]
    elif risk_level == "MODERATE":
        steps = [
            "Address partial compliance gaps",
            "Improve documentation completeness",
            "Validate MRV and traceability structure",
        ]
    else:
        steps = [
            "Finalize remaining documentation",
            "Prepare for third-party validation",
        ]

    for s in steps:
        lines.append(f"- {s}")

    lines.append("")

    return "\n".join(lines)

def build_eligibility_dossier_text(
    project_name: str,
    audit_mode: str,
    score_data: Dict[str, Any],
    score_label: str,
    results: List[Dict[str, Any]],
    project_data: Dict[str, Any],
) -> str:

    score = score_data.get("score", 0)
    compliant = score_data.get("compliant", 0)
    partial = score_data.get("partial", 0)
    non_compliant = score_data.get("non_compliant", 0)
    error = score_data.get("error", 0)

    # -------------------------
    # Elegibilidade geral
    # -------------------------
    if score >= 70:
        eligibility_status = "ELIGIBLE"
    elif score >= 40:
        eligibility_status = "CONDITIONALLY ELIGIBLE"
    else:
        eligibility_status = "NOT ELIGIBLE"

    # -------------------------
    # Extração de blocos chave
    # -------------------------
    eligibility = project_data.get("eligibility", {})
    feedstock = project_data.get("feedstock", {})
    production = project_data.get("production", {})
    storage = project_data.get("storage", {})
    ghg = project_data.get("ghg_accounting", {})
    mrv = project_data.get("monitoring_reporting", {})

    # -------------------------
    # Itens críticos
    # -------------------------
    critical_issues = []
    missing_logic = []

    for r in results or []:
        status = str(r.get("status", "")).lower()
        req_id = r.get("requirement_id", "")
        title = r.get("title", "")
        notes = r.get("notes", []) or []

        note_txt = " ".join([str(n) for n in notes]) if isinstance(notes, list) else str(notes)

        if status == "non_compliant":
            critical_issues.append(f"{req_id} — {title} | {note_txt}")

        if status == "error":
            missing_logic.append(f"{req_id} — {title}")

    critical_issues = critical_issues[:8]
    missing_logic = missing_logic[:8]

    # -------------------------
    # Construção do texto
    # -------------------------
    lines = []

    lines.append("CO2mply | Eligibility Dossier")
    lines.append("")
    lines.append(f"Project: {project_name or 'Unnamed'}")
    lines.append(f"Audit Mode: {str(audit_mode).capitalize()}")
    lines.append("")
    
    # STATUS
    lines.append("1. Eligibility Status")
    lines.append(f"- Status: {eligibility_status}")
    lines.append(f"- Compliance Score: {score}")
    lines.append(f"- Rating: {score_label}")
    lines.append("")

    # INTERPRETAÇÃO
    lines.append("2. Eligibility Interpretation")

    if eligibility_status == "NOT ELIGIBLE":
        lines.append(
            "The project does not currently meet minimum eligibility requirements under the selected methodology. "
            "Critical structural elements are missing or not evidenced."
        )
    elif eligibility_status == "CONDITIONALLY ELIGIBLE":
        lines.append(
            "The project may become eligible subject to targeted corrections and additional documentation."
        )
    else:
        lines.append(
            "The project demonstrates sufficient alignment with eligibility requirements and may proceed to validation."
        )

    lines.append("")

    # COMPONENTES
    lines.append("3. Core Eligibility Components")

    lines.append(f"- Net-negative claim: {eligibility.get('net_negative_claim')}")
    lines.append(f"- Additionality claim: {eligibility.get('additionality_claim')}")
    lines.append(f"- Durability (years): {eligibility.get('durability_years')}")
    lines.append("")

    # FEEDSTOCK
    lines.append("4. Feedstock Assessment")
    lines.append(f"- Biomass type: {feedstock.get('biomass_type')}")
    lines.append(f"- Pre-project use: {feedstock.get('pre_project_biomass_use')}")
    lines.append("")

    # PRODUÇÃO
    lines.append("5. Production System")
    lines.append(f"- Technology: {production.get('pyrolysis_technology')}")
    lines.append(f"- Reactor diagram provided: {production.get('reactor_design_diagram')}")
    lines.append("")

    # STORAGE
    lines.append("6. Storage & Permanence")
    lines.append(f"- Storage module: {storage.get('storage_module')}")
    lines.append(f"- Storage stability: {storage.get('storage_environment_stable')}")
    lines.append("")

    # GHG
    lines.append("7. GHG Accounting Structure")
    lines.append(f"- System boundary defined: {ghg.get('system_boundary_defined')}")
    lines.append(f"- Baseline defined: {ghg.get('baseline_defined')}")
    lines.append("")

    # MRV
    lines.append("8. MRV Readiness")
    lines.append(f"- Monitoring plan: {mrv.get('monitoring_plan')}")
    lines.append(f"- Verification readiness: {mrv.get('verification_ready')}")
    lines.append("")

    # RISCOS
    lines.append("9. Key Eligibility Risks")

    if critical_issues:
        for c in critical_issues:
            lines.append(f"- {c}")
    else:
        lines.append("- No critical risks identified.")

    lines.append("")

    # COBERTURA DA ENGINE
    lines.append("10. Engine Coverage Limitations")
    lines.append(
        "Some requirements were not evaluated due to missing logic bindings in the engine. "
        "These appear as 'error' and should not be interpreted as non-compliance."
    )
    lines.append(f"- Requirements not evaluated: {error}")
    lines.append("")

    # RECOMENDAÇÕES
    lines.append("11. Recommended Actions")

    if eligibility_status == "NOT ELIGIBLE":
        actions = [
            "Define storage pathway and permanence approach",
            "Establish MRV system",
            "Demonstrate net-negative emissions",
        ]
    elif eligibility_status == "CONDITIONALLY ELIGIBLE":
        actions = [
            "Complete missing documentation",
            "Strengthen traceability and MRV",
        ]
    else:
        actions = [
            "Proceed to validation",
            "Prepare audit documentation package",
        ]

    for a in actions:
        lines.append(f"- {a}")

    lines.append("")

    return "\n".join(lines)

def build_investor_dossier_text(
    project_name: str,
    audit_mode: str,
    score_data: Dict[str, Any],
    score_label: str,
    results: List[Dict[str, Any]],
    project_data: Dict[str, Any],
) -> str:

    score = score_data.get("score", 0)
    compliant = score_data.get("compliant", 0)
    partial = score_data.get("partial", 0)
    non_compliant = score_data.get("non_compliant", 0)
    error = score_data.get("error", 0)
    applicable = score_data.get("applicable_requirements", 0)

    eligibility = project_data.get("eligibility", {})
    feedstock = project_data.get("feedstock", {})
    production = project_data.get("production", {})
    storage = project_data.get("storage", {})
    methodology = project_data.get("methodology", {})
    monitoring = project_data.get("monitoring_reporting", {})
    management = project_data.get("management", {})

    if score >= 75:
        investment_readiness = "HIGH"
    elif score >= 50:
        investment_readiness = "MODERATE"
    else:
        investment_readiness = "LOW"

    major_risks = []
    partial_gaps = []
    logic_gaps = []

    for r in results or []:
        status = str(r.get("status", "")).strip().lower()
        req_id = str(r.get("requirement_id", "")).strip()
        req_name = str(r.get("requirement_name", "")).strip() or str(r.get("title", "")).strip()
        notes = r.get("notes", []) or []

        if isinstance(notes, list):
            note_text = " ".join([str(n) for n in notes if str(n).strip()])
        else:
            note_text = str(notes).strip()

        line = f"{req_id} — {req_name}"
        if note_text:
            line += f" | {note_text}"

        if status == "non_compliant":
            major_risks.append(line)
        elif status == "partial":
            partial_gaps.append(line)
        elif status == "error":
            logic_gaps.append(line)

    major_risks = major_risks[:6]
    partial_gaps = partial_gaps[:6]
    logic_gaps = logic_gaps[:6]

    lines = []

    lines.append("CO2mply | Investor Dossier")
    lines.append("")
    lines.append(f"Project: {project_name or 'Unnamed project'}")
    lines.append(f"Audit Mode: {str(audit_mode).capitalize()}")
    lines.append("")

    lines.append("1. Investment Snapshot")
    lines.append(f"- Compliance Score: {score}")
    lines.append(f"- Rating: {score_label}")
    lines.append(f"- Investment Readiness: {investment_readiness}")
    lines.append(f"- Applicable Requirements Reviewed: {applicable}")
    lines.append("")

    lines.append("2. Executive Positioning")
    if investment_readiness == "LOW":
        lines.append(
            "The project is not yet positioned for investment-grade diligence. "
            "Core compliance and documentation gaps remain material."
        )
    elif investment_readiness == "MODERATE":
        lines.append(
            "The project shows promising structural elements, but still requires targeted de-risking "
            "before it can be considered investment-ready."
        )
    else:
        lines.append(
            "The project demonstrates strong compliance alignment and appears suitable for advanced diligence."
        )
    lines.append("")

    lines.append("3. Structural Strengths")
    lines.append(f"- Methodology standard: {methodology.get('standard')}")
    lines.append(f"- Pathway: {methodology.get('pathway')}")
    lines.append(f"- Feedstock defined: {feedstock.get('biomass_type')}")
    lines.append(f"- Pre-project feedstock use: {feedstock.get('pre_project_biomass_use')}")
    lines.append(f"- Technology defined: {production.get('pyrolysis_technology')}")
    lines.append(f"- Reactor diagram provided: {production.get('reactor_design_diagram')}")
    lines.append(f"- Durability years: {eligibility.get('durability_years')}")
    lines.append("")

    lines.append("4. Diligence Risk Profile")
    lines.append(f"- Compliant requirements: {compliant}")
    lines.append(f"- Partial requirements: {partial}")
    lines.append(f"- Non-compliant requirements: {non_compliant}")
    lines.append(f"- Logic coverage gaps: {error}")
    lines.append("")

    lines.append("5. Principal Risk Drivers")
    if major_risks:
        for item in major_risks:
            lines.append(f"- {item}")
    else:
        lines.append("- No principal non-compliance drivers identified.")
    lines.append("")

    lines.append("6. Improvement Track")
    if partial_gaps:
        for item in partial_gaps:
            lines.append(f"- {item}")
    else:
        lines.append("- No material partial gaps identified.")
    lines.append("")

    lines.append("7. Monitoring & Governance Signals")
    lines.append(f"- Monitoring plan: {monitoring.get('monitoring_plan')}")
    lines.append(f"- Verification readiness: {monitoring.get('verification_ready')}")
    lines.append(f"- Adaptive management plan: {management.get('adaptive_management_plan')}")
    lines.append(f"- Emergency response plan: {management.get('emergency_response_plan')}")
    lines.append("")

    lines.append("8. Storage & Permanence Signals")
    lines.append(f"- Storage pathway: {methodology.get('storage_pathway')}")
    lines.append(f"- Storage module: {storage.get('storage_module')}")
    lines.append(f"- Storage environment stable: {storage.get('storage_environment_stable')}")
    lines.append(f"- Storage monitoring plan: {storage.get('storage_monitoring_plan')}")
    lines.append("")

    lines.append("9. Engine Coverage Note")
    lines.append(
        "Some requirements remain outside active deterministic evaluation and are currently reported as logic gaps. "
        "These should be interpreted as diligence blind spots rather than automatic project failure."
    )
    if logic_gaps:
        lines.append("- Sample logic gaps:")
        for item in logic_gaps:
            lines.append(f"  - {item}")
    lines.append("")

    lines.append("10. Investor-Oriented Recommendation")
    if investment_readiness == "LOW":
        recommendations = [
            "Do not position the project as validation-ready yet.",
            "Prioritize resolution of non-compliant eligibility, storage, and MRV items.",
            "Close critical documentary and governance gaps before external diligence.",
        ]
    elif investment_readiness == "MODERATE":
        recommendations = [
            "Advance with controlled diligence only.",
            "Resolve core non-compliant items before investor-facing positioning.",
            "Strengthen MRV, storage, and traceability evidence.",
        ]
    else:
        recommendations = [
            "Proceed to advanced diligence.",
            "Package the project with methodology, MRV, and traceability evidence.",
            "Prepare validation roadmap and investment memo.",
        ]

    for rec in recommendations:
        lines.append(f"- {rec}")

    lines.append("")
    return "\n".join(lines)

# =========================================================
# RENDER RESULTADO V2
# =========================================================

structured_v2_output = st.session_state.get("structured_v2_output")

if structured_v2_output:

    st.markdown("---")
    st.subheader("Resultado da Auditoria Estruturada")

    results = structured_v2_output.get("results", [])
    project_data = structured_v2_output.get("project_data", {})
    normalized_fields = structured_v2_output.get("normalized_fields", [])
    score_data = structured_v2_output.get("score_data", {})
    score_label = structured_v2_output.get("score_label", "")
    audit_mode = structured_v2_output.get("audit_mode", st.session_state.get("audit_mode", "development"))

    summary_text = build_structured_audit_summary_text(
        project_name=project_name,
        audit_mode=audit_mode,
        score_data=score_data,
        score_label=score_label,
        results=results,
    )

    dossier_text = build_eligibility_dossier_text(
        project_name=project_name,
        audit_mode=audit_mode,
        score_data=score_data,
        score_label=score_label,
        results=results,
        project_data=project_data,
    )

    investor_dossier_text = build_investor_dossier_text(
        project_name=project_name,
        audit_mode=audit_mode,
        score_data=score_data,
        score_label=score_label,
        results=results,
        project_data=project_data,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Compliance Score", f"{score_data.get('score', 0):.1f}")

    with col2:
        st.metric("Rating", score_label)

    if results:

        normalized_results = []

        for r in results:
            item = dict(r)
            item["score"] = item.get("requirement_score", item.get("score", 0))
            item["confidence"] = item.get("confidence", 0)
            normalized_results.append(item)

        try:
            df = build_audit_dataframe(normalized_results)

            st.markdown("### Matriz de Conformidade")
            st.dataframe(df, hide_index=True, width="stretch")

        except Exception as e:
            import traceback
            st.error(f"Erro ao montar matriz: {e}")
            st.code(traceback.format_exc(), language="python")
            df = None

        if df is not None:
            try:
                # -------------------------
                # TITLES
                # -------------------------
                matrix_title = f"CO2mply | Compliance Matrix | {str(audit_mode).capitalize()}"
                summary_title = f"CO2mply | Audit Summary | {str(audit_mode).capitalize()}"
                dossier_title = f"CO2mply | Eligibility Dossier | {str(audit_mode).capitalize()}"
                investor_dossier_title = f"CO2mply | Investor Dossier | {str(audit_mode).capitalize()}"

                # -------------------------
                # MATRIZ
                # -------------------------
                matrix_pdf = matrix_to_pdf_bytes(df, title=matrix_title)
                matrix_docx = matrix_to_docx_bytes(df, title=matrix_title)

                # -------------------------
                # SUMMARY
                # -------------------------
                summary_pdf = pdf_from_text(summary_title, summary_text)
                summary_docx = docx_from_text(summary_title, summary_text)

                # -------------------------
                # DOSSIER
                # -------------------------
                dossier_pdf = pdf_from_text(dossier_title, dossier_text)
                dossier_docx = docx_from_text(dossier_title, dossier_text)

                # -------------------------
                # INVESTOR DOSSIER
                # -------------------------
                investor_dossier_pdf = pdf_from_text(
                    investor_dossier_title,
                    investor_dossier_text
                )
                investor_dossier_docx = docx_from_text(
                    investor_dossier_title,
                    investor_dossier_text
                )

                # -------------------------
                # DOWNLOADS
                # -------------------------
                d1, d2, d3, d4, d5, d6, d7, d8 = st.columns(8)

                with d1:
                    st.download_button(
                        "Matriz (.pdf)",
                        data=matrix_pdf,
                        file_name=f"matriz_v2_{audit_mode}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                with d2:
                    st.download_button(
                        "Matriz (.docx)",
                        data=matrix_docx,
                        file_name=f"matriz_v2_{audit_mode}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

                with d3:
                    st.download_button(
                        "Summary (.pdf)",
                        data=summary_pdf,
                        file_name=f"audit_summary_v2_{audit_mode}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                with d4:
                    st.download_button(
                        "Summary (.docx)",
                        data=summary_docx,
                        file_name=f"audit_summary_v2_{audit_mode}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

                with d5:
                    st.download_button(
                        "Dossier (.pdf)",
                        data=dossier_pdf,
                        file_name=f"eligibility_dossier_v2_{audit_mode}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                with d6:
                    st.download_button(
                        "Dossier (.docx)",
                        data=dossier_docx,
                        file_name=f"eligibility_dossier_v2_{audit_mode}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

                with d7:
                    st.download_button(
                        "Investor (.pdf)",
                        data=investor_dossier_pdf,
                        file_name=f"investor_dossier_v2_{audit_mode}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                with d8:
                    st.download_button(
                        "Investor (.docx)",
                        data=investor_dossier_docx,
                        file_name=f"investor_dossier_v2_{audit_mode}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

            except Exception as e:
                import traceback
                st.error(f"Erro ao gerar downloads: {e}")
                st.code(traceback.format_exc(), language="python")

    else:
        st.warning("Nenhum resultado retornado pela engine.")

    with st.expander("Audit Summary"):
        st.text(summary_text)

    with st.expander("Eligibility Dossier"):
        st.text(dossier_text)

    with st.expander("Investor Dossier"):
        st.text(investor_dossier_text)

    with st.expander("Project Data (extraído)"):
        st.write(project_data)

    with st.expander("Normalized Fields"):
        st.write(normalized_fields)

    with st.expander("Payload completo"):
        st.write(structured_v2_output)
        
# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    if current_user and current_user.get("email"):
        render_project_manager(current_user["email"])

    st.markdown("### Configurações")

    if st.session_state.get("current_project_name"):
        st.markdown("---")
        st.success(f"Projeto ativo: {st.session_state['current_project_name']}")

    if st.session_state.get("current_methodology"):
        st.info(f"Metodologia: {st.session_state['current_methodology']}")

    language_choice = st.selectbox(
        t(lang, "language_label"),
        options=["Português", "English"],
        index=0 if st.session_state["language"] == "pt" else 1,
    )

    new_lang = "pt" if language_choice == "Português" else "en"
    if new_lang != st.session_state["language"]:
        st.session_state["language"] = new_lang
        st.rerun()

    lang = st.session_state.get("language", "pt")
    st.session_state["language"] = lang

    menu = st.selectbox(
        "Menu",
        [
            "Dashboard",
            "All Projects",
            "Create Project",
            "Chat Técnico",
            "Pre-Feasibility",
            "Full Feasibility",
            "Verification",
            "Data Room",
            "Document Filler",
            "Spreadsheet Filler",
            "Methodology Library",
            "Settings",
            "Audit History",
            "User Access",
        ],
        index=0,
    )

    st.write("**Banco de dados:**")
    st.caption(f"DB module: {DB_MODULE_AVAILABLE}")
    st.caption(f"DB ok: {DB_CONNECTION_OK}")

    if DB_CONNECTION_ERROR:
        st.caption(f"DB error: {DB_CONNECTION_ERROR}")

    if db_is_configured():
        st.success("Banco conectado e pronto para uso")
    else:
        st.error("Banco não disponível")
        if DB_CONNECTION_ERROR:
            st.caption(DB_CONNECTION_ERROR)

    if current_user.get("auth_mode") == "oidc" and auth_available():
        if st.button("Sair", use_container_width=True, key="sidebar_logout"):
            st.logout()

    st.divider()
    show_sources = st.checkbox(t(lang, "show_sources"), value=True)
    show_snippets = st.checkbox(t(lang, "show_snippets"), value=True)
    show_attributes = st.checkbox(t(lang, "show_attributes"), value=False)

    st.divider()
    usage = get_usage(current_user["email"])
    limits = get_role_limits(current_role)

    st.write("**Uso do mês**")
    st.dataframe(
        pd.DataFrame([
            {"Ação": "Chat", "Usado": usage["chat"], "Limite": limits["chat"]},
            {"Ação": "Audit", "Usado": usage["full_audit"], "Limite": limits["full_audit"]},
        ]),
        hide_index=True,
        use_container_width=True
    )

    st.divider()
    st.write("**Custo estimado da sessão**")
    st.metric("USD", f"{st.session_state['audit_session_cost_estimate']:.3f}")

    if st.button(t(lang, "clear_session"), use_container_width=True):
        for key, value in DEFAULT_STATE.items():
            st.session_state[key] = value
        st.rerun()



# =========================================================
# FILE SEARCH RESULT HELPERS
# =========================================================

def extract_file_search_results(response, source_label: str = "") -> List[Dict[str, Any]]:
    results = []

    if response is None:
        return results

    output = getattr(response, "output", None) or []

    for item in output:
        if getattr(item, "type", None) != "file_search_call":
            continue

        search_results = getattr(item, "results", None) or []

        for r in search_results:
            filename = getattr(r, "filename", None) or "Documento sem nome"
            score = getattr(r, "score", None) or 0.0

            text = ""
            page = None

            content = getattr(r, "content", None) or []
            if content:
                text_parts = []
                for c in content:
                    c_text = getattr(c, "text", None)
                    if c_text:
                        text_parts.append(str(c_text))

                    c_page = getattr(c, "page", None)
                    if c_page is not None and page is None:
                        page = c_page

                text = "\n".join(text_parts).strip()

            if not text:
                text = getattr(r, "text", None) or ""

            results.append({
                "source_label": source_label,
                "filename": filename,
                "page": page,
                "text": text,
                "score": score,
            })

    return results


def deduplicate_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped = []
    seen = set()

    for s in sources:
        key = (
            str(s.get("filename") or "").strip().lower(),
            str(s.get("page") or "").strip().lower(),
            str(s.get("text") or "").strip().lower(),
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(s)

    return deduped


def get_response_text(response) -> str:
    if response is None:
        return ""

    text = getattr(response, "output_text", None)
    if text:
        return str(text)

    output = getattr(response, "output", None) or []

    collected = []

    for item in output:
        content = getattr(item, "content", None) or []
        for c in content:
            c_text = getattr(c, "text", None)
            if c_text:
                collected.append(str(c_text))

    return "\n".join(collected).strip()
# =========================================================
# CHAT MODE
# =========================================================

def call_file_search_for_store(
    messages: List[Dict[str, str]],
    vector_store_id: str,
    max_results: int,
    extra_system_prompt: Optional[str] = None,
):
    system_text = BASE_SYSTEM_PROMPT + "\n\n" + CHAT_SYSTEM_PROMPT
    if extra_system_prompt:
        system_text += "\n\n" + extra_system_prompt

    return client.responses.create(
        model=MODEL_NAME,
        input=[{"role": "system", "content": system_text}] + messages,
        temperature=0,
        include=["file_search_call.results"],
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": max_results,
            }
        ],
    )


def call_reasoning_over_context(user_content: str):
    return client.responses.create(
        model=MODEL_NAME,
        input=[
            {
                "role": "system",
                "content": BASE_SYSTEM_PROMPT + "\n\n" + AUDIT_REASONING_PROMPT
            },
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )


def build_combined_context_prompt(
    user_question: str,
    project_sources: List[Dict[str, Any]],
    methodology_sources: List[Dict[str, Any]],
) -> str:
    project_block = []
    for i, src in enumerate(project_sources, start=1):
        project_block.append(
            "[PROJETO "
            + str(i)
            + "] Documento: "
            + safe_str(src.get("filename"))
            + " | Página/Seção: "
            + safe_str(src.get("page") or "não identificada")
            + "\nTrecho:\n"
            + sanitize_xml_text(src.get("text") or "")
            + "\n"
        )

    methodology_block = []
    for i, src in enumerate(methodology_sources, start=1):
        methodology_block.append(
            "[METODOLOGIA "
            + str(i)
            + "] Documento: "
            + safe_str(src.get("filename"))
            + " | Página/Seção: "
            + safe_str(src.get("page") or "não identificada")
            + "\nTrecho:\n"
            + sanitize_xml_text(src.get("text") or "")
            + "\n"
        )

    project_text = "\n".join(project_block) if project_block else "Nenhum trecho de projeto recuperado."
    methodology_text = "\n".join(methodology_block) if methodology_block else "Nenhum trecho metodológico recuperado."

    prompt = (
        "Pergunta do usuário:\n"
        + safe_str(user_question)
        + "\n\n"
        + "Responda à pergunta usando EXCLUSIVAMENTE os trechos abaixo.\n"
        + "Compare explicitamente Projeto × Metodologia quando aplicável.\n"
        + "Não use conhecimento externo.\n\n"
        + "======================\n"
        + "TRECHOS DO PROJETO\n"
        + "======================\n"
        + project_text
        + "\n\n"
        + "======================\n"
        + "TRECHOS DA METODOLOGIA\n"
        + "======================\n"
        + methodology_text
    )

    return sanitize_xml_text(prompt)


def render_chat_mode():
    project_vs_id = st.session_state.get("current_project_vector_store_id")
    methodology_vs_id = st.session_state.get("current_methodology_vector_store_id")

    if not project_vs_id or not methodology_vs_id:
        st.error("Selecione um projeto antes de usar o chat ou a auditoria.")
        st.stop()

    show_sources = st.session_state.get("show_sources", True)
    show_attributes = st.session_state.get("show_attributes", False)
    show_snippets = st.session_state.get("show_snippets", True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Faça uma pergunta")

    if user_input:
        if not can_consume(current_user["email"], current_role, "chat"):
            st.error("Limite do chat atingido.")
            return

        consume_usage(current_user["email"], "chat")

        st.session_state.messages.append({
            "role": "user",
            "content": sanitize_xml_text(user_input),
        })

        project_id = st.session_state.get("current_project_id")
        if project_id:
            try:
                save_chat_message(
                    project_id=project_id,
                    user_email=current_user["email"],
                    role="user",
                    message=sanitize_xml_text(user_input),
                )
            except Exception:
                pass

        with st.chat_message("user"):
            st.markdown(user_input)

        final_answer = ""
        project_sources = []
        methodology_sources = []
        all_sources = []

        with st.chat_message("assistant"):
            with st.spinner("Buscando evidências..."):
                try:
                    project_search_response = call_file_search_for_store(
                        messages=st.session_state.messages,
                        vector_store_id=project_vs_id,
                        max_results=PROJECT_MAX_RESULTS,
                        extra_system_prompt="Recupere evidências da documentação do projeto relevantes para a pergunta."
                    )
                    project_sources = extract_file_search_results(project_search_response, "Projeto")

                    methodology_search_response = call_file_search_for_store(
                        messages=st.session_state.messages,
                        vector_store_id=methodology_vs_id,
                        max_results=METHODOLOGY_MAX_RESULTS,
                        extra_system_prompt="Recupere requisitos e critérios metodológicos relevantes para a pergunta."
                    )
                    methodology_sources = extract_file_search_results(methodology_search_response, "Metodologia")

                    project_sources_rankable = normalize_sources(project_sources, "project")
                    methodology_sources_rankable = normalize_sources(methodology_sources, "methodology")

                    ranked_sources = rank_sources(
                        user_input,
                        project_sources_rankable + methodology_sources_rankable,
                    )

                    combined_prompt = build_smart_context(
                        user_input,
                        ranked_sources,
                        max_items=8,
                    )

                    answer_response = call_reasoning_over_context(
                        user_content=combined_prompt
                    )
                    answer_text = get_response_text(answer_response).strip()

                    if not answer_text:
                        answer_text = "A base de conhecimento não contém informação suficiente para responder com segurança."

                    st.markdown(answer_text)

                    all_sources = deduplicate_sources(project_sources + methodology_sources)

                    if show_sources:
                        render_sources_block("Fontes do Projeto", project_sources, show_attributes, show_snippets)
                        render_sources_block("Fontes da Metodologia", methodology_sources, show_attributes, show_snippets)

                    st.session_state["last_answer_text"] = sanitize_xml_text(answer_text)
                    st.session_state["last_sources_project"] = project_sources
                    st.session_state["last_sources_methodology"] = methodology_sources
                    st.session_state["last_sources_all"] = all_sources
                    final_answer = answer_text

                except Exception as e:
                    final_answer = f"Erro ao consultar a AuditorIA: {str(e)}"
                    st.error(final_answer)

        if project_id:
            try:
                save_audit_output(
                    project_id=project_id,
                    user_email=current_user["email"],
                    output_type="chat_answer",
                    title="Resposta do chat técnico",
                    question=user_input,
                    answer=final_answer,
                    content=final_answer,
                )
            except Exception:
                pass

        st.session_state.messages.append({
            "role": "assistant",
            "content": sanitize_xml_text(final_answer),
        })

        if project_id:
            try:
                save_chat_message(
                    project_id=project_id,
                    user_email=current_user["email"],
                    role="assistant",
                    message=sanitize_xml_text(final_answer),
                )
            except Exception:
                pass

# =========================================================
# FULL AUDIT MODE HELPERS
# =========================================================

def get_engine_params_for_mode(execution_mode: str) -> Dict[str, int]:
    if execution_mode == t(lang, "fast_mode"):
        return {
            "module_project_queries": 2,
            "module_methodology_queries": 2,
            "project_max_results_per_query": 3,
            "methodology_max_results_per_query": 3,
            "max_project_hits_in_prompt": 4,
            "max_methodology_hits_in_prompt": 4,
            "max_text_chars_per_hit": 900,
        }

    return {
        "module_project_queries": 4,
        "module_methodology_queries": 4,
        "project_max_results_per_query": 5,
        "methodology_max_results_per_query": 5,
        "max_project_hits_in_prompt": 8,
        "max_methodology_hits_in_prompt": 8,
        "max_text_chars_per_hit": 1800,
    }


def estimate_audit_effort(
    execution_mode: str,
    selected_scopes: List[str],
    selected_requirements_count: int
) -> Dict[str, Any]:
    scope_count = len(selected_scopes)

    if execution_mode == t(lang, "fast_mode"):
        if scope_count <= 1 and selected_requirements_count <= 10:
            level = "baixo"
        elif scope_count <= 2 and selected_requirements_count <= 18:
            level = "medio"
        else:
            level = "alto"
    else:
        if scope_count <= 1 and selected_requirements_count <= 10:
            level = "medio"
        elif scope_count <= 2 and selected_requirements_count <= 18:
            level = "alto"
        else:
            level = "muito alto"

    hard_stop = execution_mode == t(lang, "complete_mode") and (
        scope_count >= 4 or selected_requirements_count >= 30
    )
    needs_confirmation = level in {"alto", "muito alto"}

    return {
        "level": level,
        "hard_stop": hard_stop,
        "needs_confirmation": needs_confirmation,
    }


def render_progress_box():
    state = st.session_state["progress_state"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t(lang, "progress"), f"{state.get('percent', 0)}%")
    col2.metric(t(lang, "current_module"), safe_str(state.get("module", "")) or "-")
    col3.metric(t(lang, "current_step"), safe_str(state.get("stage", "")) or "-")
    col4.metric(
        t(lang, "cost_estimate"),
        f"US$ {float(state.get('execution_estimated_cost', 0.0)):.3f}"
    )
    st.progress(int(state.get("percent", 0)))
    if state.get("message"):
        st.caption(state["message"])


def append_history_entry(
    run_id: str,
    project_name: str,
    execution_mode: str,
    selected_modules: List[str],
    summary: Dict[str, Any],
    estimated_cost: float,
):
    st.session_state["audit_history"].insert(
        0,
        {
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "run_id": run_id,
            "project_name": project_name,
            "execution_mode": execution_mode,
            "modules": selected_modules,
            "module_count": len(selected_modules),
            "overall_score": summary.get("overall_score", 0),
            "overall_confidence": summary.get("overall_confidence", 0),
            "estimated_cost": estimated_cost,
            "status_counts": summary.get("status_counts", {}),
        }
    )

def apply_matrix_filters(
    df: pd.DataFrame,
    module_filter: List[str],
    status_filter: List[str],
    risk_filter: List[str]
) -> pd.DataFrame:
    out = df.copy()

    if not out.empty:
        if module_filter:
            out = out[out["module"].isin(module_filter)]
        if status_filter:
            out = out[out["status"].isin(status_filter)]
        if risk_filter:
            out = out[out["risk"].isin(risk_filter)]

    return out


def make_progress_callback(progress_container, status_container):
    def _callback(payload: Dict[str, Any]):
        st.session_state["progress_state"] = payload
        with progress_container:
            render_progress_box()
        with status_container:
            pass

    return _callback
    
# =========================================================
# FULL AUDIT MODE
# =========================================================

# =========================================================
# AUDIT SCOPE MAPPING
# =========================================================

    
def render_full_audit_mode():
    project_vs_id = st.session_state.get("current_project_vector_store_id")
    methodology_vs_id = st.session_state.get("current_methodology_vector_store_id")

    if not project_vs_id or not methodology_vs_id:
        st.error("Selecione um projeto antes de usar o chat ou a auditoria.")
        st.stop()

    st.markdown(f"### {t(lang, 'full_audit_mode')}")

    requirements = get_requirements()

    all_modules = sorted(list({r["module"] for r in requirements})) if requirements else []
    available_scopes = get_available_audit_scopes(requirements)
    default_scopes = get_default_audit_scopes(available_scopes)

    with st.expander("Configuração", expanded=True):
        project_name = st.text_input(
            t(lang, "project_name"),
            value=st.session_state.get("current_project_name") or ""
        )

        selected_scopes = st.multiselect(
            "Audit scope",
            options=available_scopes,
            default=default_scopes,
            help=(
                "Core Integrity is the methodological foundation of the audit. "
                "Eligibility is always enforced internally even if scope selection changes."
            ),
        )

        selected_modules = resolve_selected_modules_from_scope(
            requirements=requirements,
            selected_scopes=selected_scopes,
        )

        st.session_state["structured_selected_modules"] = selected_modules

        selected_requirements = [
            r for r in requirements
            if r["module"] in selected_modules
        ]
        st.caption(
            "Modules covered in this run: "
            + (", ".join(selected_modules) if selected_modules else "none")
        )

        if selected_scopes:
            st.markdown(get_scope_help_text(selected_scopes))

        with st.expander("Requirements covered in this run", expanded=False):
            for scope in selected_scopes:
                scope_modules = AUDIT_SCOPE_CONFIG.get(scope, {}).get("modules", [])
                scope_requirements = [
                    r for r in selected_requirements
                    if r["module"] in scope_modules
                ]

                if not scope_requirements:
                    continue

                st.markdown(f"**{scope}**")
                for req in scope_requirements:
                    st.markdown(f"- `{req['id']}` — {req['title']}")

        execution_mode = st.radio(
            t(lang, "execution_mode"),
            [t(lang, "fast_mode"), t(lang, "complete_mode")],
            horizontal=True,
            index=0
        )

        show_trails = st.checkbox(
            t(lang, "show_trails"),
            value=False,
            key="show_trails_full_audit"
        )

    if not selected_scopes:
        st.warning("Selecione pelo menos um escopo de auditoria para continuar.")
        return

    selected_requirements_count = len(selected_requirements)
    engine_params = get_engine_params_for_mode(execution_mode)
    effort = estimate_audit_effort(execution_mode, selected_scopes, selected_requirements_count)

    temp_engine = AuditEngine(
        api_key=OPENAI_API_KEY,
        model=MODEL_NAME,
        project_vector_store_id=project_vs_id or "",
        methodology_vector_store_id=methodology_vs_id,
        project_name=project_name,
        requirements=requirements,
        module_project_queries=engine_params["module_project_queries"],
        module_methodology_queries=engine_params["module_methodology_queries"],
        project_max_results_per_query=engine_params["project_max_results_per_query"],
        methodology_max_results_per_query=engine_params["methodology_max_results_per_query"],
        max_project_hits_in_prompt=engine_params["max_project_hits_in_prompt"],
        max_methodology_hits_in_prompt=engine_params["max_methodology_hits_in_prompt"],
        max_text_chars_per_hit=engine_params["max_text_chars_per_hit"],
    )

    cost_estimate = temp_engine.estimate_run_cost(
        selected_modules=selected_modules,
        execution_mode=execution_mode
    )

    cost_estimate = temp_engine.estimate_run_cost(
        selected_modules=selected_modules,
        execution_mode=execution_mode
    )

    min_cost = float(cost_estimate.get("estimated_min_cost", 0.0))
    max_cost = float(cost_estimate.get("estimated_max_cost", 0.0))

    cost_range_text = f"US$ {min_cost:.3f} – {max_cost:.3f}"

    st.markdown(f"#### {t(lang, 'estimated_effort')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nível", effort["level"].upper())
    c2.metric("Escopos", len(selected_scopes))
    c3.metric("Requisitos", selected_requirements_count)
    c4.metric("Custo estimado", cost_range_text)

    st.caption(
        f"Auditando {len(selected_modules)} módulos internos distribuídos em {len(selected_scopes)} escopo(s)."
    )
    if effort["hard_stop"]:
        st.error("Execução bloqueada preventivamente: reduza módulos ou use o modo rápido.")

    confirm_run = True
    if effort["needs_confirmation"] and not effort["hard_stop"]:
        confirm_run = st.checkbox(
            "Confirmo que desejo executar esta auditoria mesmo com esforço/custo estimado elevado."
        )

    progress_container = st.empty()
    status_container = st.empty()
    with progress_container:
        render_progress_box()

    run_disabled = (
        not can_consume(current_user["email"], current_role, "full_audit")
        or effort["hard_stop"]
        or not confirm_run
    )

    col_run1, col_run2 = st.columns([1, 1])

    with col_run1:
        run_button = st.button(
            t(lang, "run_audit"),
            type="primary",
            use_container_width=True,
            disabled=run_disabled
        )

    if False:
        pass

    if False:
        pass

    st.info("Fluxo legado de validation desativado.")

# =========================================================
# LEGACY PAGE BRIDGES
# =========================================================

st.session_state["_validation_legacy_renderer"] = None

# =========================================================
# ROUTER
# =========================================================

if menu == "Dashboard":
    dashboard.render()

elif menu == "All Projects":
    all_projects.render()

elif menu == "Create Project":
    create_project.render()

elif menu == "Chat Técnico":
    render_chat_mode()

elif menu == "Pre-Feasibility":
    pre_feasibility.render()

elif menu == "Full Feasibility":
    full_feasibility.render()

elif menu == "Validation":
    st.info("Validation legado desativado.")

elif menu == "Verification":
    verification.render()

elif menu == "Data Room":
    data_room.render()

elif menu == "Document Filler":
    document_filler.render()

elif menu == "Spreadsheet Filler":
    spreadsheet_filler.render()

elif menu == "Methodology Library":
    methodology_library.render()

elif menu == "Settings":
    settings_page.render()

elif menu == "Audit History":
    audit_history_page.render()

elif menu == "User Access":
    user_access_page.render()
