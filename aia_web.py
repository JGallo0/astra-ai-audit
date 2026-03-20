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
    validation,
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

MODEL_NAME = get_config_value("OPENAI_MODEL", "gpt-4.1")

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


def set_current_project(project: dict, user_email: str = ""):
    st.session_state["current_project_id"] = project.get("id")
    st.session_state["current_project_name"] = project.get("project_name")
    st.session_state["current_methodology"] = project.get("methodology")
    st.session_state["current_project_vector_store_id"] = project.get("project_vector_store_id")
    st.session_state["current_methodology_vector_store_id"] = project.get("methodology_vector_store_id")

    # 🔥 NOVO: carregar histórico do chat do banco
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

        except Exception as e:
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
        key="project_selector"
    )

selected_methodology = st.sidebar.selectbox(
        "Selecionar metodologia",
        options=methodology_options,
        index=default_methodology_index,
        format_func=lambda x: METHODOLOGY_REGISTRY[x]["label"],
        key="methodology_selector"
    )

    if st.sidebar.button("Ativar análise", key="activate_project_button"):
        set_current_project(
            project_options[selected_project_label],
            user_email,
            methodology_key=selected_methodology,
        )
        st.rerun()

    if st.session_state.get("current_project_name") or st.session_state.get("current_methodology"):
        st.sidebar.markdown("---")
        st.sidebar.success(
            f"Projeto ativo: **{st.session_state.get('current_project_name') or '-'}**"
        )
        st.sidebar.info(
            f"Metodologia ativa: **{METHODOLOGY_REGISTRY.get(st.session_state.get('current_methodology', ''), {}).get('label', '-')}**"
        )

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
            st.image(logo_path, width=340)
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

active_methodology_label = METHODOLOGY_REGISTRY.get(
    st.session_state.get("current_methodology", ""),
    {}
).get("label", "-")

if st.session_state.get("current_project_name"):
    st.info(
        f"Projeto ativo: {st.session_state.get('current_project_name')} | "
        f"Metodologia: {active_methodology_label}"
    )
else:
    st.warning("Nenhum projeto selecionado.")
# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    if current_user and current_user.get("email"):
        render_project_manager(current_user["email"])

    st.markdown("### Configurações")

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
            "Validation",
            "Verification",
            "Data Room",
            "Document Filler",
            "Spreadsheet Filler",
            "Methodology Library",
            "Settings",
            "Audit History",
            "User Access",
        ],
        index=6,
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
    selected_modules: List[str],
    selected_requirements_count: int
) -> Dict[str, Any]:
    module_count = len(selected_modules)

    if execution_mode == t(lang, "fast_mode"):
        if module_count <= 2 and selected_requirements_count <= 10:
            level = "baixo"
        elif module_count <= 4 and selected_requirements_count <= 18:
            level = "medio"
        else:
            level = "alto"
    else:
        if module_count <= 2 and selected_requirements_count <= 10:
            level = "medio"
        elif module_count <= 4 and selected_requirements_count <= 18:
            level = "alto"
        else:
            level = "muito alto"

    hard_stop = execution_mode == t(lang, "complete_mode") and (
        module_count >= 5 or selected_requirements_count >= 20
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

def render_full_audit_mode():
    project_vs_id = st.session_state.get("current_project_vector_store_id")
    methodology_vs_id = st.session_state.get("current_methodology_vector_store_id")

    if not project_vs_id or not methodology_vs_id:
        st.error("Selecione um projeto antes de usar o chat ou a auditoria.")
        st.stop()

    st.markdown(f"### {t(lang, 'full_audit_mode')}")

    requirements = get_requirements_for_methodology(
        st.session_state.get("current_methodology")
    )

    all_modules = sorted(list({r["module"] for r in requirements})) if requirements else []

    with st.expander("Configuração", expanded=True):
        project_name = st.text_input(
            t(lang, "project_name"),
            value=st.session_state.get("current_project_name") or ""
        )

        selected_modules = st.multiselect(
            t(lang, "modules_to_audit"),
            options=all_modules,
            default=all_modules[:2] if len(all_modules) >= 2 else all_modules
        )

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

    st.session_state["current_project_name"] = project_name

    if not requirements:
        st.warning("A metodologia selecionada ainda não possui matriz estruturada de requisitos no app.")
        return

    if not selected_modules:
        st.warning("Selecione pelo menos um módulo para auditar.")
        return

    selected_requirements_count = len([r for r in requirements if r["module"] in selected_modules])
    engine_params = get_engine_params_for_mode(execution_mode)
    effort = estimate_audit_effort(execution_mode, selected_modules, selected_requirements_count)

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

    st.markdown(f"#### {t(lang, 'estimated_effort')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nível", safe_str(effort["level"]).upper())
    c2.metric("Módulos", len(selected_modules))
    c3.metric("Requisitos", selected_requirements_count)
    c4.metric(
        t(lang, "cost_estimate"),
        f"US$ {cost_estimate['estimated_min_cost']:.3f} – {cost_estimate['estimated_max_cost']:.3f}"
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

    has_previous = bool(st.session_state.get("last_full_audit_results"))

    with col_run2:
        rerun_failures = st.button(
            t(lang, "reanalyze_failures"),
            use_container_width=True,
            disabled=not has_previous
        )

    if run_button:
        consume_usage(current_user["email"], "full_audit")
        callback = make_progress_callback(progress_container, status_container)

        try:
            engine = AuditEngine(
                api_key=OPENAI_API_KEY,
                model=MODEL_NAME,
                requirements=requirements,
                project_vector_store_id=project_vs_id,
                methodology_vector_store_id=methodology_vs_id,
                project_name=project_name,
                module_project_queries=engine_params["module_project_queries"],
                module_methodology_queries=engine_params["module_methodology_queries"],
                project_max_results_per_query=engine_params["project_max_results_per_query"],
                methodology_max_results_per_query=engine_params["methodology_max_results_per_query"],
                max_project_hits_in_prompt=engine_params["max_project_hits_in_prompt"],
                max_methodology_hits_in_prompt=engine_params["max_methodology_hits_in_prompt"],
                max_text_chars_per_hit=engine_params["max_text_chars_per_hit"],
                progress_callback=callback,
            )
            with st.spinner("Executando auditoria..."):
                audit_output = engine.run_full_audit(
                    selected_modules=selected_modules,
                    enable_auto_reanalysis=True,
                )

            results = audit_output["results"]
            trails = audit_output["trails"]
            summary = engine.summarize_results(results)
            df = build_audit_dataframe(results)

            st.session_state["last_full_audit_results"] = results
            st.session_state["last_full_audit_trails"] = trails
            st.session_state["last_full_audit_summary"] = summary
            st.session_state["last_full_audit_df"] = df
            st.session_state["last_full_audit_run_id"] = audit_output["run_id"]
            st.session_state["audit_session_cost_estimate"] += float(audit_output.get("estimated_cost", 0.0))
            st.session_state["progress_state"]["execution_estimated_cost"] = float(audit_output.get("estimated_cost", 0.0))
            st.session_state["progress_state"]["session_estimated_cost"] = float(st.session_state["audit_session_cost_estimate"])

            append_history_entry(
                run_id=audit_output["run_id"],
                project_name=project_name,
                execution_mode=execution_mode,
                selected_modules=selected_modules,
                summary=summary,
                estimated_cost=float(audit_output.get("estimated_cost", 0.0)),
            )

            st.success("Auditoria concluída com sucesso.")

            project_id = st.session_state.get("current_project_id")
            if project_id:
                try:
                    save_audit_output(
                        project_id=project_id,
                        user_email=current_user["email"],
                        output_type="full_audit",
                        title="Auditoria completa",
                        question=project_name,
                        answer=str(summary),
                        content=str(results),
                    )
                except Exception:
                    pass

        except Exception as e:
            st.error(f"Erro ao executar auditoria: {str(e)}")

    if rerun_failures and has_previous:
        callback = make_progress_callback(progress_container, status_container)

        try:
            engine = AuditEngine(
                api_key=OPENAI_API_KEY,
                model=MODEL_NAME,
                requirements=requirements,
                project_vector_store_id=project_vs_id,
                methodology_vector_store_id=methodology_vs_id,
                project_name=project_name,
                module_project_queries=3,
                module_methodology_queries=3,
                project_max_results_per_query=4,
                methodology_max_results_per_query=4,
                max_project_hits_in_prompt=5,
                max_methodology_hits_in_prompt=5,
                max_text_chars_per_hit=1100,
                progress_callback=callback,
            )

            with st.spinner("Reanalisando falhas..."):
                rerun_output = engine.rerun_failed_items(
                    previous_results=st.session_state["last_full_audit_results"],
                    selected_modules=selected_modules,
                )

            rerun_results = rerun_output["results"]
            prev_results = st.session_state["last_full_audit_results"]
            prev_by_id = {safe_str(x.get("requirement_id", "")): x for x in prev_results}

            for item in rerun_results:
                prev_by_id[safe_str(item.get("requirement_id", ""))] = item

            merged_results = list(prev_by_id.values())
            merged_results = sorted(
                merged_results,
                key=lambda x: (safe_str(x.get("module", "")), safe_str(x.get("requirement_id", "")))
            )

            summary = engine.summarize_results(merged_results)
            df = build_audit_dataframe(merged_results)

            st.session_state["last_full_audit_results"] = merged_results
            st.session_state["last_full_audit_trails"] += rerun_output["trails"]
            st.session_state["last_full_audit_summary"] = summary
            st.session_state["last_full_audit_df"] = df
            st.session_state["last_full_audit_run_id"] = rerun_output["run_id"]
            st.session_state["audit_session_cost_estimate"] += float(rerun_output.get("estimated_cost", 0.0))
            st.session_state["progress_state"]["execution_estimated_cost"] = float(rerun_output.get("estimated_cost", 0.0))
            st.session_state["progress_state"]["session_estimated_cost"] = float(st.session_state["audit_session_cost_estimate"])

            append_history_entry(
                run_id=rerun_output["run_id"],
                project_name=project_name,
                execution_mode="Reanálise",
                selected_modules=selected_modules,
                summary=summary,
                estimated_cost=float(rerun_output.get("estimated_cost", 0.0)),
            )

            st.success("Falhas reanalisadas com sucesso.")

            project_id = st.session_state.get("current_project_id")
            if project_id:
                try:
                    save_audit_output(
                        project_id=project_id,
                        user_email=current_user["email"],
                        output_type="full_audit_rerun",
                        title="Reanálise de falhas",
                        question=project_name,
                        answer=str(summary),
                        content=str(merged_results),
                    )
                except Exception:
                    pass

        except Exception as e:
            st.error(f"Erro ao reanalisar falhas: {str(e)}")

if isinstance(st.session_state.get("last_full_audit_df"), pd.DataFrame) and not st.session_state["last_full_audit_df"].empty:
    df = st.session_state["last_full_audit_df"].copy()
    summary = st.session_state["last_full_audit_summary"]
    trails = st.session_state["last_full_audit_trails"]
    run_id = st.session_state["last_full_audit_run_id"]
    project_name = st.session_state.get("current_project_name") or "Projeto sem nome"

    tab_summary, tab_matrix, tab_details, tab_downloads, tab_history = st.tabs([
        t(lang, "summary_tab"),
        t(lang, "matrix_tab"),
        t(lang, "details_tab"),
        t(lang, "downloads_tab"),
        t(lang, "history_tab"),
    ])

    with tab_summary:
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Requisitos", summary.get("total_requirements", 0))
        s2.metric("Score geral", f"{summary.get('overall_score', 0)}%")
        s3.metric("Confiança geral", f"{summary.get('overall_confidence', 0)}%")
        s4.metric(t(lang, "session_cost"), f"US$ {st.session_state['audit_session_cost_estimate']:.3f}")

        st.markdown("#### Módulos")
        module_scores = summary.get("module_scores", {})
        module_conf = summary.get("module_confidence", {})
        if module_scores:
            module_df = pd.DataFrame([
                {
                    "Módulo": mod,
                    "Score": module_scores.get(mod, 0),
                    "Confiança": module_conf.get(mod, 0),
                }
                for mod in sorted(module_scores.keys())
            ])
            st.dataframe(module_df, hide_index=True, use_container_width=True)

        st.markdown("#### Status")
        status_df = pd.DataFrame([
            {"Status": k, "Quantidade": v}
            for k, v in (summary.get("status_counts", {}) or {}).items()
        ])
        st.dataframe(status_df, hide_index=True, use_container_width=True)

        st.markdown("#### Risco")
        risk_df = pd.DataFrame([
            {"Risco": k, "Quantidade": v}
            for k, v in (summary.get("risk_counts", {}) or {}).items()
        ])
        st.dataframe(risk_df, hide_index=True, use_container_width=True)

    with tab_matrix:
        st.markdown(f"#### {t(lang, 'filters')}")
        f1, f2, f3 = st.columns(3)

        module_options = sorted(df["module"].dropna().unique().tolist()) if "module" in df.columns else []
        status_options = sorted(df["status"].dropna().unique().tolist()) if "status" in df.columns else []
        risk_options = sorted(df["risk"].dropna().unique().tolist()) if "risk" in df.columns else []

        with f1:
            module_filter = st.multiselect(
                t(lang, "module_filter"),
                options=module_options,
                default=st.session_state["current_filters"]["module"],
            )
        with f2:
            status_filter = st.multiselect(
                t(lang, "status_filter"),
                options=status_options,
                default=st.session_state["current_filters"]["status"],
            )
        with f3:
            risk_filter = st.multiselect(
                t(lang, "risk_filter"),
                options=risk_options,
                default=st.session_state["current_filters"]["risk"],
            )

        st.session_state["current_filters"] = {
            "module": module_filter,
            "status": status_filter,
            "risk": risk_filter,
        }

        filtered_df = apply_matrix_filters(df, module_filter, status_filter, risk_filter)
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    with tab_details:
        detail_df = apply_matrix_filters(
            df,
            st.session_state["current_filters"]["module"],
            st.session_state["current_filters"]["status"],
            st.session_state["current_filters"]["risk"],
        )

        st.markdown("#### Requisitos em detalhe")
        for _, row in detail_df.iterrows():
            title = f"{safe_str(row.get('requirement_id', ''))} — {safe_str(row.get('title', ''))}"
            with st.expander(title):
                st.markdown(
                    status_badge(safe_str(row.get("status", ""))) + " " + risk_badge(safe_str(row.get("risk", ""))),
                    unsafe_allow_html=True
                )

                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Módulo:** {safe_str(row.get('module', ''))}")
                    st.write(f"**Score:** {safe_str(row.get('score', ''))}")
                with c2:
                    st.write(f"**Confiança:** {safe_str(row.get('confidence', ''))}")

                st.markdown("**Base metodológica**")
                st.write(safe_str(row.get("methodology_basis", "")) or "Não identificado.")

                st.markdown("**Evidência do projeto**")
                st.write(safe_str(row.get("project_evidence", "")) or "Não identificado.")

                st.markdown("**Gap**")
                st.write(safe_str(row.get("gap", "")) or "Não identificado.")

                st.markdown("**Recomendação**")
                st.write(safe_str(row.get("recommendation", "")) or "Não identificado.")

                if safe_str(row.get("notes", "")).strip():
                    st.markdown("**Notas**")
                    st.write(safe_str(row.get("notes", "")))

    with tab_downloads:
        full_audit_text = build_full_audit_text(summary, st.session_state["last_full_audit_results"])
        full_audit_docx = docx_from_text("Auditoria Resumida Isometric", full_audit_text)
        full_audit_pdf = pdf_from_text("Auditoria Resumida Isometric", full_audit_text)

        eligibility_dossier_text = build_full_eligibility_dossier_text(
            project_name=project_name,
            summary=summary,
            results=st.session_state["last_full_audit_results"],
            trails=st.session_state["last_full_audit_trails"],
        )
        eligibility_docx = docx_from_text("Dossiê de Elegibilidade Metodológica", eligibility_dossier_text)
        eligibility_pdf = pdf_from_text("Dossiê de Elegibilidade Metodológica", eligibility_dossier_text)

        matrix_docx = matrix_to_docx_bytes(df, "Matriz de Conformidade Isometric")
        matrix_pdf = matrix_to_pdf_bytes(df, "Matriz de Conformidade Isometric")
        csv_bytes = convert_df_to_csv_bytes(df)
        json_bytes = convert_json_to_bytes({
            "run_id": run_id,
            "summary": summary,
            "results": st.session_state["last_full_audit_results"],
            "trails": st.session_state["last_full_audit_trails"],
        })
        eligibility_docx = docx_from_text("Dossiê de Elegibilidade Metodológica", eligibility_dossier_text)
        eligibility_pdf = pdf_from_text("Dossiê de Elegibilidade Metodológica", eligibility_dossier_text)

        matrix_docx = matrix_to_docx_bytes(df, "Matriz de Conformidade Isometric")
        matrix_pdf = matrix_to_pdf_bytes(df, "Matriz de Conformidade Isometric")
        csv_bytes = convert_df_to_csv_bytes(df)
        json_bytes = convert_json_to_bytes({
            "run_id": run_id,
            "summary": summary,
            "results": st.session_state["last_full_audit_results"],
            "trails": st.session_state["last_full_audit_trails"],
        })

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                "Auditoria resumida (.md)",
                data=full_audit_text,
                file_name=f"auditoria_resumida_isometric_{run_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
            st.download_button(
                "Dossiê (.md)",
                data=eligibility_dossier_text,
                file_name=f"dossie_elegibilidade_{run_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
            st.download_button(
                "Matriz (.csv)",
                data=csv_bytes,
                file_name=f"matriz_conformidade_isometric_{run_id}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with d2:
            st.download_button(
                "Auditoria resumida (.docx)",
                data=full_audit_docx,
                file_name=f"auditoria_resumida_isometric_{run_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            st.download_button(
                "Dossiê (.docx)",
                data=eligibility_docx,
                file_name=f"dossie_elegibilidade_{run_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            st.download_button(
                "Matriz (.docx)",
                data=matrix_docx,
                file_name=f"matriz_conformidade_isometric_{run_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        with d3:
            st.download_button(
                "Auditoria resumida (.pdf)",
                data=full_audit_pdf,
                file_name=f"auditoria_resumida_isometric_{run_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.download_button(
                "Dossiê (.pdf)",
                data=eligibility_pdf,
                file_name=f"dossie_elegibilidade_{run_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.download_button(
                "Matriz (.pdf)",
                data=matrix_pdf,
                file_name=f"matriz_conformidade_isometric_{run_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.download_button(
                "Trilha (.json)",
                data=json_bytes,
                file_name=f"auditoria_isometric_{run_id}.json",
                mime="application/json",
                use_container_width=True
            )

if st.session_state.get("show_trails_full_audit", False):
    st.markdown("#### Trilha detalhada")
    for i, trail in enumerate(trails, start=1):
        with st.expander(f"[{i}] {trail.get('module', '')} | {trail.get('analysis_label', '')}"):
            st.markdown("**Queries do projeto**")
            st.code(trail.get("project_query", ""), language="text")
            st.markdown("**Queries da metodologia**")
            st.code(trail.get("methodology_query", ""), language="text")
            st.markdown("**Trechos do projeto**")
            st.code(trail.get("project_context", ""), language="text")
            st.markdown("**Trechos da metodologia**")
            st.code(trail.get("methodology_context", ""), language="text")
            st.markdown("**Resposta bruta do modelo**")
            st.code(trail.get("model_response_raw", ""), language="json")
            st.markdown("**Resultado interpretado**")
            st.json(trail.get("parsed_result", {}))

    with tab_history:
        st.markdown(f"#### {t(lang, 'history')}")
        history = st.session_state.get("audit_history", [])
        if not history:
            st.info("Nenhuma execução registrada nesta sessão.")
        else:
            for item in history:
                html_parts = [
                    '<div class="auditoria-card">',
                    '<div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;">',
                    '<div>',
                    f'<div style="font-weight:700;color:{THEME["primary"]};">{safe_str(item["project_name"])}</div>',
                    f'<div class="auditoria-small">{safe_str(item["timestamp"])}</div>',
                    '</div>',
                    f'<div class="auditoria-small">run_id: {safe_str(item["run_id"])}</div>',
                    '</div>',
                    '<div style="margin-top:0.5rem;">',
                    badge_html(safe_str(item["execution_mode"]), "info"),
                    badge_html(f"score {item['overall_score']}%", "success"),
                    badge_html(f"conf {item['overall_confidence']}%", "warning"),
                    badge_html(f"US$ {item['estimated_cost']:.3f}", "danger"),
                    '</div>',
                    '<div class="auditoria-small" style="margin-top:0.5rem;">',
                    f'módulos: {", ".join(item["modules"])}',
                    '</div>',
                    '</div>',
                ]
                html = "".join(html_parts)
                st.markdown(html, unsafe_allow_html=True)
else:
    st.info("Execute a auditoria completa para gerar a matriz de conformidade.")
    
        # =========================================================
# LEGACY PAGE BRIDGES
# =========================================================

st.session_state["_validation_legacy_renderer"] = render_full_audit_mode

# =========================================================
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
    validation.render()

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
