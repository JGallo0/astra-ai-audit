import io
import json
import os
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from audit_engine import AuditEngine
from isometric_requirements import ISOMETRIC_REQUIREMENTS

try:
    from db import execute as db_execute, fetch as db_fetch
    DB_MODULE_AVAILABLE = True
except Exception:
    db_execute = None
    db_fetch = None
    DB_MODULE_AVAILABLE = False

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


OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada em st.secrets nem no .env")

MODEL_NAME = get_config_value("OPENAI_MODEL", "gpt-4.1")

PROJECT_VECTOR_STORE_ID = get_config_value(
    "PROJECT_VECTOR_STORE_ID",
    "vs_69b4035175c48191ae87cbfcf0663248"
)

METHODOLOGY_VECTOR_STORE_ID = get_config_value(
    "METHODOLOGY_VECTOR_STORE_ID",
    "vs_69b310b246c08191a7eb5b13c1977787"
)

LOGO_PATH = get_config_value("ASTRACARBON_LOGO_PATH", "assets/logo_astracarbon.jpg")

AUTH_REQUIRED = get_bool_config("AUTH_REQUIRED", False)
ALLOW_LOCAL_BYPASS = get_bool_config("ALLOW_LOCAL_BYPASS", True)

ALLOWED_EMAILS = get_list_config("ALLOWED_EMAILS", [])
ALLOWED_DOMAINS = get_list_config("ALLOWED_DOMAINS", [])
ADMIN_EMAILS = get_list_config("ADMIN_EMAILS", [])
INTERNAL_DOMAINS = get_list_config("INTERNAL_DOMAINS", [])

DEFAULT_ROLE = get_config_value("DEFAULT_ROLE", "pilot_client")

ADMIN_CHAT_LIMIT = get_int_config("ADMIN_CHAT_LIMIT", 9999)
ADMIN_STRUCTURED_AUDIT_LIMIT = get_int_config("ADMIN_STRUCTURED_AUDIT_LIMIT", 9999)
ADMIN_REPORT_LIMIT = get_int_config("ADMIN_REPORT_LIMIT", 9999)
ADMIN_MATRIX_LIMIT = get_int_config("ADMIN_MATRIX_LIMIT", 9999)
ADMIN_DEEP_DIVE_LIMIT = get_int_config("ADMIN_DEEP_DIVE_LIMIT", 9999)
ADMIN_FULL_AUDIT_LIMIT = get_int_config("ADMIN_FULL_AUDIT_LIMIT", 9999)

INTERNAL_CHAT_LIMIT = get_int_config("INTERNAL_CHAT_LIMIT", 500)
INTERNAL_STRUCTURED_AUDIT_LIMIT = get_int_config("INTERNAL_STRUCTURED_AUDIT_LIMIT", 100)
INTERNAL_REPORT_LIMIT = get_int_config("INTERNAL_REPORT_LIMIT", 100)
INTERNAL_MATRIX_LIMIT = get_int_config("INTERNAL_MATRIX_LIMIT", 100)
INTERNAL_DEEP_DIVE_LIMIT = get_int_config("INTERNAL_DEEP_DIVE_LIMIT", 100)
INTERNAL_FULL_AUDIT_LIMIT = get_int_config("INTERNAL_FULL_AUDIT_LIMIT", 50)

PILOT_CHAT_LIMIT = get_int_config("PILOT_CHAT_LIMIT", 50)
PILOT_STRUCTURED_AUDIT_LIMIT = get_int_config("PILOT_STRUCTURED_AUDIT_LIMIT", 10)
PILOT_REPORT_LIMIT = get_int_config("PILOT_REPORT_LIMIT", 10)
PILOT_MATRIX_LIMIT = get_int_config("PILOT_MATRIX_LIMIT", 10)
PILOT_DEEP_DIVE_LIMIT = get_int_config("PILOT_DEEP_DIVE_LIMIT", 10)
PILOT_FULL_AUDIT_LIMIT = get_int_config("PILOT_FULL_AUDIT_LIMIT", 5)

APP_NAME = "AuditorIA"
APP_SUBTITLE = "Auditor técnico documental de projetos de biochar e créditos de carbono"

client = OpenAI(api_key=OPENAI_API_KEY)

PROJECT_MAX_RESULTS = 12
METHODOLOGY_MAX_RESULTS = 12

SYSTEM_PROMPT = """
Você é a AuditorIA, auditora técnica da AstraCarbon especializada em projetos de remoção de carbono via biochar.

Seu objetivo é analisar EXCLUSIVAMENTE os documentos disponíveis na base de conhecimento.

A base possui dois tipos de documentos:
1) Documentação do projeto
2) Documentação metodológica

REGRAS OBRIGATÓRIAS:
- Utilize SOMENTE informações recuperadas da base de documentos.
- Não utilize conhecimento geral do modelo.
- Não invente dados.
- Não preencha lacunas com suposições.
- Não conclua conformidade plena sem evidência documental.
- Diferencie claramente:
  1. ausência documental
  2. inconsistência documental
  3. potencial não conformidade
- Sempre compare Projeto × Metodologia quando a pergunta exigir auditoria.

PROCESSO DE ANÁLISE:
1) Identifique evidências no projeto.
2) Identifique requisitos da metodologia.
3) Compare ambos.
4) Identifique lacunas e inconsistências.
5) Avalie o nível de risco.

SE NÃO HOUVER INFORMAÇÃO SUFICIENTE:
Escreva exatamente:
"A base de conhecimento não contém informação suficiente para responder com segurança."

SE DOCUMENTOS APRESENTAREM CONFLITO:
Escreva exatamente:
"Inconsistência documental identificada."

FORMATO OBRIGATÓRIO DA RESPOSTA:
1. Evidências encontradas nos documentos
2. Requisitos metodológicos relevantes
3. Lacunas documentais
4. Inconsistências documentais
5. Potenciais não conformidades
6. Recomendações técnicas
7. Nível de risco

Se algum item não tiver conteúdo, escreva:
"Não identificado na base consultada."
"""

JSON_AUDIT_PROMPT = """
Você deve responder em JSON VÁLIDO, sem texto antes ou depois.

Use exclusivamente os documentos recuperados da base.

Estrutura obrigatória:
{
  "pergunta": "string",
  "evidencias_encontradas": [
    {
      "documento": "string",
      "pagina": "string",
      "trecho": "string"
    }
  ],
  "requisitos_metodologicos": [
    {
      "documento": "string",
      "pagina_ou_secao": "string",
      "trecho": "string"
    }
  ],
  "lacunas_documentais": ["string"],
  "inconsistencias_documentais": ["string"],
  "potenciais_nao_conformidades": ["string"],
  "recomendacoes_tecnicas": ["string"],
  "nivel_risco": "baixo|medio|alto"
}

REGRAS:
- Se não houver evidência suficiente, registre isso explicitamente.
- Não invente páginas.
- Se a página não estiver disponível, use "não identificada".
- Não use markdown.
- Não use conhecimento externo.
"""

REPORT_PROMPT = """
Você deve produzir um RELATÓRIO CONSOLIDADO DE AUDITORIA, em texto claro e estruturado.

Use exclusivamente os documentos recuperados e, quando disponível, a auditoria JSON já produzida.

Objetivo do relatório:
- sintetizar as evidências do projeto
- sintetizar os requisitos metodológicos relevantes
- destacar lacunas documentais
- destacar inconsistências documentais
- destacar potenciais não conformidades
- priorizar recomendações técnicas
- apresentar uma conclusão executiva com o nível de risco

FORMATO OBRIGATÓRIO:
# Relatório Consolidado de Auditoria

## 1. Escopo analisado
## 2. Evidências documentais do projeto
## 3. Requisitos metodológicos relevantes
## 4. Lacunas documentais
## 5. Inconsistências documentais
## 6. Potenciais não conformidades
## 7. Recomendações priorizadas
## 8. Conclusão executiva

REGRAS:
- Não use conhecimento externo.
- Não invente fatos.
- Se faltar evidência, declare isso explicitamente.
- Seja objetivo, técnico e auditável.
"""

COMPLIANCE_MATRIX_PROMPT = """
Você deve responder em JSON VÁLIDO, sem texto antes ou depois.

Objetivo:
Construir uma MATRIZ DE CONFORMIDADE comparando evidências do projeto com requisitos metodológicos.

Use exclusivamente os documentos recuperados.

Estrutura obrigatória:
{
  "pergunta": "string",
  "matriz_conformidade": [
    {
      "requisito": "string",
      "documento_metodologia": "string",
      "pagina_ou_secao_metodologia": "string",
      "evidencia_projeto": "string",
      "documento_projeto": "string",
      "pagina_projeto": "string",
      "status": "atende|atende_parcialmente|nao_identificado|potencial_nao_conformidade|inconsistencia",
      "risco": "baixo|medio|alto",
      "recomendacao": "string"
    }
  ]
}
"""

DEEP_DIVE_PROMPT = """
Você deve realizar um APROFUNDAMENTO TÉCNICO de uma não conformidade, lacuna documental ou inconsistência.

Use exclusivamente:
- os trechos do projeto
- os trechos da metodologia
- a auditoria já produzida
- a matriz de conformidade já produzida

Objetivo:
explicar como o projeto pode evoluir até a plena conformidade metodológica.

FORMATO OBRIGATÓRIO:
# Aprofundamento Técnico da Não Conformidade

## 1. Item analisado
## 2. Por que esse item representa risco metodológico
## 3. Evidências atualmente existentes
## 4. O que está faltando para plena conformidade
## 5. Melhorias documentais necessárias
## 6. Melhorias técnicas / operacionais / MRV necessárias
## 7. Evidências adicionais recomendadas para auditoria
## 8. Plano de ação prioritário
## 9. Condição mínima para considerar o item metodologicamente robusto

REGRAS:
- Não use conhecimento externo.
- Não invente fatos.
- Se faltar informação, declare isso explicitamente.
- Seja específico e corretivo, não genérico.
"""

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🔥",
    layout="wide"
)

st.title(f"🔥 {APP_NAME}")
st.caption(APP_SUBTITLE)

# =========================================================
# SESSION
# =========================================================

DEFAULT_STATE = {
    "messages": [],
    "last_sources_project": [],
    "last_sources_methodology": [],
    "last_sources_all": [],
    "last_answer_text": "",
    "last_audit_json": None,
    "last_report_text": "",
    "last_compliance_matrix_json": None,
    "last_deep_dive_text": "",
    "last_user_question": "",
    "last_full_audit_results": [],
    "last_full_audit_trails": [],
    "last_full_audit_summary": {},
    "last_full_audit_df": pd.DataFrame(),
    "last_full_audit_run_id": "",
    "usage_counters": {},
    "current_project_name": "Projeto Nova Esperança",
    "db_status_message": "",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# HELPERS
# =========================================================

def _is_valid_xml_char(ch: str) -> bool:
    cp = ord(ch)
    return (
        cp == 0x9
        or cp == 0xA
        or cp == 0xD
        or (0x20 <= cp <= 0xD7FF)
        or (0xE000 <= cp <= 0xFFFD)
        or (0x10000 <= cp <= 0x10FFFF)
    )


def sanitize_xml_text(text: Any) -> str:
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if _is_valid_xml_char(ch))
    return text


def safe_str(value: Any) -> str:
    return sanitize_xml_text("" if value is None else str(value))


def safe_get(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def normalize_content_item(content_item: Any) -> str:
    if isinstance(content_item, str):
        return sanitize_xml_text(content_item)

    if isinstance(content_item, dict):
        if "text" in content_item and isinstance(content_item["text"], str):
            return sanitize_xml_text(content_item["text"])
        if "content" in content_item and isinstance(content_item["content"], list):
            texts = []
            for sub in content_item["content"]:
                if isinstance(sub, dict) and "text" in sub:
                    texts.append(sanitize_xml_text(sub["text"]))
            return "\n".join(texts).strip()

    text_attr = getattr(content_item, "text", None)
    if isinstance(text_attr, str):
        return sanitize_xml_text(text_attr)

    return ""


def get_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return sanitize_xml_text(output_text.strip())

    parts = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) == "message":
            for content_item in getattr(item, "content", []) or []:
                text = normalize_content_item(content_item)
                if text:
                    parts.append(text)

    return "\n\n".join(parts).strip()


def extract_page_from_result(result: Any) -> Optional[str]:
    attrs = safe_get(result, "attributes", {}) or {}
    possible_keys = [
        "page",
        "page_number",
        "page_index",
        "start_page",
        "end_page",
        "pagina",
        "página",
        "section",
        "secao",
        "seção",
        "heading",
    ]
    for key in possible_keys:
        if key in attrs and attrs[key] is not None:
            return safe_str(attrs[key])
    return None


def extract_result_text(result: Any) -> str:
    content = safe_get(result, "content", None)

    if isinstance(content, list):
        texts = []
        for item in content:
            item_type = safe_get(item, "type", None)
            item_text = safe_get(item, "text", None)
            if item_type == "text" and item_text:
                texts.append(sanitize_xml_text(item_text))
        if texts:
            return "\n".join(texts).strip()

    direct_text = safe_get(result, "text", None)
    if isinstance(direct_text, str) and direct_text.strip():
        return sanitize_xml_text(direct_text.strip())

    return ""


def extract_file_search_results(response: Any, source_group: str) -> List[Dict[str, Any]]:
    extracted = []

    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) != "file_search_call":
            continue

        for result in getattr(item, "results", []) or []:
            extracted.append(
                {
                    "source_group": safe_str(source_group),
                    "file_id": safe_get(result, "file_id", None),
                    "filename": safe_str(
                        safe_get(result, "filename", None)
                        or safe_get(result, "file_name", None)
                        or "Documento sem nome"
                    ),
                    "score": safe_get(result, "score", None),
                    "text": extract_result_text(result),
                    "attributes": safe_get(result, "attributes", {}) or {},
                    "page": extract_page_from_result(result),
                }
            )

    return extracted


def deduplicate_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []

    for src in sources:
        key = (
            src.get("source_group"),
            src.get("file_id"),
            src.get("filename"),
            src.get("page"),
            (src.get("text") or "")[:300],
        )
        if key not in seen:
            seen.add(key)
            unique.append(src)

    return unique


def try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    text = sanitize_xml_text(text).strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            return None

    return None


def render_sources_block(title: str, sources: List[Dict[str, Any]], show_attributes: bool, show_snippets: bool):
    st.subheader(title)

    if not sources:
        st.info("Nenhuma fonte foi retornada.")
        return

    for i, src in enumerate(sources, start=1):
        page_display = src.get("page") or "não identificada"
        label = f"{i}. {src['filename']} — pág./seção: {page_display}"

        with st.expander(label):
            st.write(f"**Grupo:** {src.get('source_group')}")
            st.write(f"**Score:** {src.get('score')}")
            st.write(f"**File ID:** {src.get('file_id')}")
            if show_attributes and src.get("attributes"):
                st.json(src["attributes"])
            if show_snippets and src.get("text"):
                st.markdown("**Trecho recuperado:**")
                st.code(src["text"])


def export_sources_markdown(sources: List[Dict[str, Any]]) -> str:
    lines = ["# Fontes utilizadas", ""]
    for i, src in enumerate(sources, start=1):
        lines.append(f"## {i}. {safe_str(src['filename'])}")
        lines.append(f"- grupo: {safe_str(src.get('source_group'))}")
        lines.append(f"- file_id: {safe_str(src.get('file_id'))}")
        lines.append(f"- score: {safe_str(src.get('score'))}")
        lines.append(f"- página/seção: {safe_str(src.get('page') or 'não identificada')}")
        if src.get("attributes"):
            lines.append(f"- attributes: `{sanitize_xml_text(json.dumps(src['attributes'], ensure_ascii=False))}`")
        lines.append("")
        if src.get("text"):
            lines.append("### Trecho recuperado")
            lines.append(sanitize_xml_text(src["text"]))
            lines.append("")
    return "\n".join(lines)


def render_audit_json(audit: Dict[str, Any]) -> str:
    pergunta = safe_str(audit.get("pergunta", "Não identificada"))
    evidencias = audit.get("evidencias_encontradas", []) or []
    requisitos = audit.get("requisitos_metodologicos", []) or []
    lacunas = audit.get("lacunas_documentais", []) or []
    inconsistencias = audit.get("inconsistencias_documentais", []) or []
    nao_conformidades = audit.get("potenciais_nao_conformidades", []) or []
    recomendacoes = audit.get("recomendacoes_tecnicas", []) or []
    nivel_risco = safe_str(audit.get("nivel_risco", "não identificado"))

    lines = [
        "## Pergunta analisada",
        pergunta,
        "",
        "## 1. Evidências encontradas nos documentos",
    ]

    if evidencias:
        for ev in evidencias:
            lines.append(
                f"- **{safe_str(ev.get('documento', 'Documento não identificado'))}** — pág./seção: {safe_str(ev.get('pagina', 'não identificada'))}"
            )
            lines.append(f"  - {safe_str(ev.get('trecho', 'Não identificado na base consultada.'))}")
    else:
        lines.append("- Não identificado na base consultada.")

    lines += ["", "## 2. Requisitos metodológicos relevantes"]
    if requisitos:
        for req in requisitos:
            lines.append(
                f"- **{safe_str(req.get('documento', 'Documento não identificado'))}** — pág./seção: {safe_str(req.get('pagina_ou_secao', 'não identificada'))}"
            )
            lines.append(f"  - {safe_str(req.get('trecho', 'Não identificado na base consultada.'))}")
    else:
        lines.append("- Não identificado na base consultada.")

    lines += ["", "## 3. Lacunas documentais"]
    if lacunas:
        for item in lacunas:
            lines.append(f"- {safe_str(item)}")
    else:
        lines.append("- Não identificado na base consultada.")

    lines += ["", "## 4. Inconsistências documentais"]
    if inconsistencias:
        for item in inconsistencias:
            lines.append(f"- {safe_str(item)}")
    else:
        lines.append("- Não identificado na base consultada.")

    lines += ["", "## 5. Potenciais não conformidades"]
    if nao_conformidades:
        for item in nao_conformidades:
            lines.append(f"- {safe_str(item)}")
    else:
        lines.append("- Não identificado na base consultada.")

    lines += ["", "## 6. Recomendações técnicas"]
    if recomendacoes:
        for item in recomendacoes:
            lines.append(f"- {safe_str(item)}")
    else:
        lines.append("- Não identificado na base consultada.")

    lines += ["", "## 7. Nível de risco", f"**{nivel_risco}**"]

    return "\n".join(lines)


def matrix_json_to_dataframe(matrix_json: Optional[Dict[str, Any]]) -> pd.DataFrame:
    rows = (matrix_json or {}).get("matriz_conformidade", []) or []
    if not rows:
        return pd.DataFrame(columns=[
            "requisito",
            "documento_metodologia",
            "pagina_ou_secao_metodologia",
            "evidencia_projeto",
            "documento_projeto",
            "pagina_projeto",
            "status",
            "risco",
            "recomendacao",
        ])

    safe_rows = []
    for row in rows:
        safe_rows.append({k: safe_str(v) for k, v in row.items()})
    return pd.DataFrame(safe_rows)


def flatten_markdown_to_lines(text: str) -> List[str]:
    text = sanitize_xml_text(text)
    return [sanitize_xml_text(line).rstrip() for line in text.replace("\r", "").split("\n")]


def build_audit_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(results)

    preferred_order = [
        "requirement_id",
        "module",
        "title",
        "status",
        "risk",
        "score",
        "confidence",
        "project_evidence",
        "methodology_basis",
        "gap",
        "recommendation",
        "notes",
    ]

    if df.empty:
        return pd.DataFrame(columns=preferred_order)

    existing_cols = [c for c in preferred_order if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in existing_cols]
    return df[existing_cols + remaining_cols]


def convert_df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def convert_json_to_bytes(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def build_full_audit_text(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append("AUDITORIA RESUMIDA ISOMETRIC")
    lines.append("")
    lines.append(f"Total de requisitos avaliados: {summary.get('total_requirements', 0)}")
    lines.append(f"Score geral: {summary.get('overall_score', 0)}%")
    lines.append("")
    lines.append("RESUMO POR STATUS")
    for k, v in (summary.get("status_counts", {}) or {}).items():
        lines.append(f"- {safe_str(k)}: {safe_str(v)}")
    lines.append("")
    lines.append("RESUMO POR RISCO")
    for k, v in (summary.get("risk_counts", {}) or {}).items():
        lines.append(f"- {safe_str(k)}: {safe_str(v)}")
    lines.append("")
    lines.append("SCORE POR MÓDULO")
    for k, v in (summary.get("module_scores", {}) or {}).items():
        lines.append(f"- {safe_str(k)}: {safe_str(v)}")
    lines.append("")
    lines.append("MATRIZ DETALHADA")
    lines.append("")

    for item in results:
        lines.append(f"Requisito: {safe_str(item.get('requirement_id', ''))} — {safe_str(item.get('title', ''))}")
        lines.append(f"Módulo: {safe_str(item.get('module', ''))}")
        lines.append(f"Status: {safe_str(item.get('status', ''))}")
        lines.append(f"Risco: {safe_str(item.get('risk', ''))}")
        lines.append(f"Score: {safe_str(item.get('score', ''))}")
        lines.append(f"Confiança: {safe_str(item.get('confidence', ''))}")
        lines.append(f"Evidência do projeto: {safe_str(item.get('project_evidence', ''))}")
        lines.append(f"Base metodológica: {safe_str(item.get('methodology_basis', ''))}")
        lines.append(f"Lacuna: {safe_str(item.get('gap', ''))}")
        lines.append(f"Recomendação: {safe_str(item.get('recommendation', ''))}")
        if item.get("notes"):
            lines.append(f"Notas: {safe_str(item.get('notes', ''))}")
        lines.append("")

    return "\n".join(lines)


def build_full_eligibility_dossier_text(
    project_name: str,
    summary: Dict[str, Any],
    results: List[Dict[str, Any]],
    trails: List[Dict[str, Any]],
) -> str:
    lines = []
    lines.append("# Dossiê de Elegibilidade Metodológica")
    lines.append("")
    lines.append(f"## Projeto analisado")
    lines.append(safe_str(project_name))
    lines.append("")
    lines.append("## 1. Objetivo do dossiê")
    lines.append(
        "Este documento consolida a avaliação de elegibilidade metodológica do projeto com base na auditoria completa "
        "requisito por requisito. O objetivo é apoiar diagnóstico, priorização de correções, preparação documental e "
        "tomada de decisão para submissão e auditoria externa."
    )
    lines.append("")
    lines.append("## 2. Síntese executiva")
    lines.append(f"- Total de requisitos avaliados: {summary.get('total_requirements', 0)}")
    lines.append(f"- Score geral: {summary.get('overall_score', 0)}%")
    for k, v in (summary.get("status_counts", {}) or {}).items():
        lines.append(f"- Status {safe_str(k)}: {safe_str(v)}")
    for k, v in (summary.get("risk_counts", {}) or {}).items():
        lines.append(f"- Risco {safe_str(k)}: {safe_str(v)}")
    lines.append("")
    lines.append("## 3. Score por módulo")
    for k, v in (summary.get("module_scores", {}) or {}).items():
        lines.append(f"- {safe_str(k)}: {safe_str(v)}")
    lines.append("")

    lines.append("## 4. Avaliação detalhada de elegibilidade")
    lines.append("")

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in results:
        module = safe_str(item.get("module", "Sem módulo"))
        grouped.setdefault(module, []).append(item)

    for module, items in grouped.items():
        lines.append(f"### Módulo: {module}")
        lines.append("")
        for item in items:
            req_id = safe_str(item.get("requirement_id", ""))
            title = safe_str(item.get("title", ""))
            status = safe_str(item.get("status", ""))
            risk = safe_str(item.get("risk", ""))
            score = safe_str(item.get("score", ""))
            confidence = safe_str(item.get("confidence", ""))
            project_evidence = safe_str(item.get("project_evidence", ""))
            methodology_basis = safe_str(item.get("methodology_basis", ""))
            gap = safe_str(item.get("gap", ""))
            recommendation = safe_str(item.get("recommendation", ""))
            notes = safe_str(item.get("notes", ""))

            lines.append(f"#### {req_id} — {title}")
            lines.append(f"- Status: {status}")
            lines.append(f"- Risco: {risk}")
            lines.append(f"- Score: {score}")
            lines.append(f"- Confiança: {confidence}")
            lines.append("")
            lines.append("**Base metodológica**")
            lines.append(methodology_basis or "Não identificado.")
            lines.append("")
            lines.append("**Evidência do projeto**")
            lines.append(project_evidence or "Não identificado.")
            lines.append("")
            lines.append("**Lacuna / restrição identificada**")
            lines.append(gap or "Não identificado.")
            lines.append("")
            lines.append("**Recomendação de elegibilidade**")
            lines.append(recommendation or "Não identificado.")
            lines.append("")
            if notes:
                lines.append("**Notas adicionais**")
                lines.append(notes)
                lines.append("")

    lines.append("## 5. Trilha técnica da auditoria")
    lines.append("")

    for i, trail in enumerate(trails, start=1):
        lines.append(f"### Item {i} — {safe_str(trail.get('requirement_id', ''))} — {safe_str(trail.get('title', ''))}")
        lines.append("")
        lines.append("**Query do projeto**")
        lines.append(safe_str(trail.get("project_query", "")) or "Não identificado.")
        lines.append("")
        lines.append("**Query da metodologia**")
        lines.append(safe_str(trail.get("methodology_query", "")) or "Não identificado.")
        lines.append("")
        lines.append("**Trechos recuperados do projeto**")
        lines.append(safe_str(trail.get("project_context", "")) or "Não identificado.")
        lines.append("")
        lines.append("**Trechos recuperados da metodologia**")
        lines.append(safe_str(trail.get("methodology_context", "")) or "Não identificado.")
        lines.append("")
        lines.append("**Resultado interpretado**")
        parsed = trail.get("parsed_result", {})
        if parsed:
            lines.append(sanitize_xml_text(json.dumps(parsed, ensure_ascii=False, indent=2)))
        else:
            lines.append("Não identificado.")
        lines.append("")

    lines.append("## 6. Priorização de ações")
    high_risk = [r for r in results if safe_str(r.get("risk", "")).lower() == "alto"]
    medium_risk = [r for r in results if safe_str(r.get("risk", "")).lower() == "medio"]

    lines.append("### Ações prioritárias de curto prazo")
    if high_risk:
        for item in high_risk:
            lines.append(
                f"- {safe_str(item.get('requirement_id', ''))} — {safe_str(item.get('title', ''))}: {safe_str(item.get('recommendation', ''))}"
            )
    else:
        lines.append("- Não identificado.")

    lines.append("")
    lines.append("### Ações prioritárias de médio prazo")
    if medium_risk:
        for item in medium_risk:
            lines.append(
                f"- {safe_str(item.get('requirement_id', ''))} — {safe_str(item.get('title', ''))}: {safe_str(item.get('recommendation', ''))}"
            )
    else:
        lines.append("- Não identificado.")

    lines.append("")
    lines.append("## 7. Conclusão de elegibilidade")
    lines.append(
        "A elegibilidade metodológica do projeto deve ser interpretada com base na combinação entre evidência já existente, "
        "lacunas identificadas, robustez das bases metodológicas citadas e capacidade de saneamento das não conformidades "
        "antes de eventual validação externa."
    )
    lines.append("")

    return "\n".join(lines)

# =========================================================
# DB / PERSISTENCE HELPERS
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


def get_plan_record(email: str) -> Optional[Dict[str, Any]]:
    email = safe_str(email).strip().lower()
    if not email:
        return None

    rows = db_fetch_safe(
        """
        SELECT plan_name, chat_limit, audit_limit, report_limit
        FROM plans
        WHERE lower(user_email) = %s
        ORDER BY id DESC
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
        "plan_name": row[0] if len(row) > 0 else "",
        "chat_limit": row[1] if len(row) > 1 else None,
        "audit_limit": row[2] if len(row) > 2 else None,
        "report_limit": row[3] if len(row) > 3 else None,
    }


def get_db_monthly_usage(email: str) -> Optional[Dict[str, int]]:
    email = safe_str(email).strip().lower()
    if not email:
        return None

    rows = db_fetch_safe(
        """
        SELECT action_type, COUNT(*)::int
        FROM usage_logs
        WHERE lower(user_email) = %s
          AND timestamp >= date_trunc('month', NOW())
          AND timestamp < date_trunc('month', NOW()) + interval '1 month'
        GROUP BY action_type
        """,
        (email,)
    )

    usage = {
        "chat": 0,
        "structured_audit": 0,
        "report": 0,
        "matrix": 0,
        "deep_dive": 0,
        "full_audit": 0,
    }

    if rows is None:
        return None

    for row in rows:
        if isinstance(row, dict):
            action = safe_str(row.get("action_type", "")).strip()
            count = int(row.get("count", 0) or 0)
        else:
            action = safe_str(row[0] if len(row) > 0 else "").strip()
            count = int(row[1] if len(row) > 1 else 0)
        if action in usage:
            usage[action] = count

    return usage


def log_usage_db(email: str, action: str, project_name: str = ""):
    email = safe_str(email).strip().lower()
    action = safe_str(action).strip()
    project_name = safe_str(project_name).strip()

    if not email or not action:
        return

    db_execute_safe(
        """
        INSERT INTO usage_logs (user_email, action_type, project_name, timestamp)
        VALUES (%s, %s, %s, NOW())
        """,
        (email, action, project_name)
    )

# =========================================================
# AUTH / ACCESS / USAGE
# =========================================================

def auth_available() -> bool:
    return hasattr(st, "login") and hasattr(st, "logout") and hasattr(st, "user")


def get_user_info() -> Dict[str, str]:
    if auth_available() and getattr(st.user, "is_logged_in", False):
        email = safe_str(getattr(st.user, "email", "")).strip().lower()
        name = safe_str(getattr(st.user, "name", "")).strip() or email or "Usuário autenticado"
        return {
            "is_logged_in": True,
            "email": email,
            "name": name,
            "auth_mode": "oidc"
        }

    if not AUTH_REQUIRED and ALLOW_LOCAL_BYPASS:
        return {
            "is_logged_in": True,
            "email": "local.dev@aia.local",
            "name": "Local Dev",
            "auth_mode": "local_bypass"
        }

    return {
        "is_logged_in": False,
        "email": "",
        "name": "",
        "auth_mode": "none"
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
        base_limits = {
            "chat": ADMIN_CHAT_LIMIT,
            "structured_audit": ADMIN_STRUCTURED_AUDIT_LIMIT,
            "report": ADMIN_REPORT_LIMIT,
            "matrix": ADMIN_MATRIX_LIMIT,
            "deep_dive": ADMIN_DEEP_DIVE_LIMIT,
            "full_audit": ADMIN_FULL_AUDIT_LIMIT,
        }
    elif role == "internal":
        base_limits = {
            "chat": INTERNAL_CHAT_LIMIT,
            "structured_audit": INTERNAL_STRUCTURED_AUDIT_LIMIT,
            "report": INTERNAL_REPORT_LIMIT,
            "matrix": INTERNAL_MATRIX_LIMIT,
            "deep_dive": INTERNAL_DEEP_DIVE_LIMIT,
            "full_audit": INTERNAL_FULL_AUDIT_LIMIT,
        }
    elif role == "pilot_client":
        base_limits = {
            "chat": PILOT_CHAT_LIMIT,
            "structured_audit": PILOT_STRUCTURED_AUDIT_LIMIT,
            "report": PILOT_REPORT_LIMIT,
            "matrix": PILOT_MATRIX_LIMIT,
            "deep_dive": PILOT_DEEP_DIVE_LIMIT,
            "full_audit": PILOT_FULL_AUDIT_LIMIT,
        }
    else:
        base_limits = {
            "chat": 0,
            "structured_audit": 0,
            "report": 0,
            "matrix": 0,
            "deep_dive": 0,
            "full_audit": 0,
        }

    plan = get_plan_record(current_user["email"]) if "current_user" in globals() else None
    if plan:
        if plan.get("chat_limit") is not None:
            base_limits["chat"] = int(plan["chat_limit"])
        if plan.get("audit_limit") is not None:
            base_limits["structured_audit"] = int(plan["audit_limit"])
            base_limits["matrix"] = int(plan["audit_limit"])
            base_limits["deep_dive"] = int(plan["audit_limit"])
            base_limits["full_audit"] = int(plan["audit_limit"])
        if plan.get("report_limit") is not None:
            base_limits["report"] = int(plan["report_limit"])

    return base_limits


def get_usage_bucket_key(email: str) -> str:
    month_key = datetime.now().strftime("%Y-%m")
    return f"{email.lower()}::{month_key}"


def init_usage_bucket(email: str):
    key = get_usage_bucket_key(email)
    if key not in st.session_state["usage_counters"]:
        st.session_state["usage_counters"][key] = {
            "chat": 0,
            "structured_audit": 0,
            "report": 0,
            "matrix": 0,
            "deep_dive": 0,
            "full_audit": 0,
        }


def get_usage(email: str) -> Dict[str, int]:
    db_usage = get_db_monthly_usage(email)
    if db_usage is not None:
        return db_usage

    init_usage_bucket(email)
    key = get_usage_bucket_key(email)
    return st.session_state["usage_counters"][key]


def can_consume(email: str, role: str, action: str) -> bool:
    limits = get_role_limits(role)
    usage = get_usage(email)
    return usage.get(action, 0) < limits.get(action, 0)


def consume_usage(email: str, action: str, project_name: str = ""):
    init_usage_bucket(email)
    key = get_usage_bucket_key(email)
    st.session_state["usage_counters"][key][action] = st.session_state["usage_counters"][key].get(action, 0) + 1

    if db_is_configured():
        log_usage_db(email, action, project_name)


def render_login_gate():
    user = get_user_info()

    if user["is_logged_in"]:
        return user

    st.warning("Este app requer autenticação para acesso.")
    st.markdown("Faça login para continuar.")

    if auth_available():
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Entrar com provedor padrão", use_container_width=True):
                st.login()
        with c2:
            if st.button("Entrar com Microsoft", use_container_width=True):
                st.login("microsoft")
    else:
        st.error("Autenticação não configurada no Streamlit.")
    st.stop()


def render_access_denied(email: str):
    st.error("Acesso não autorizado.")
    st.markdown(f"O usuário **{safe_str(email)}** não está liberado para usar a {APP_NAME}.")
    if auth_available() and getattr(st.user, "is_logged_in", False):
        if st.button("Sair"):
            st.logout()
    st.stop()


def render_usage_overview_in_sidebar(user: Dict[str, str], role: str):
    email = user["email"]
    usage = get_usage(email)
    limits = get_role_limits(role)

    with st.sidebar:
        st.divider()
        st.subheader("Acesso")
        st.write(f"**Usuário:** {safe_str(user['name'])}")
        st.write(f"**Email:** `{safe_str(email)}`")
        st.write(f"**Perfil:** `{safe_str(role)}`")
        st.write(f"**Modo de autenticação:** `{safe_str(user['auth_mode'])}`")

        if auth_available() and getattr(st.user, "is_logged_in", False):
            if st.button(f"Sair da {APP_NAME}", use_container_width=True):
                st.logout()

        st.divider()
        st.subheader("Uso do mês")

        usage_df = pd.DataFrame([
            {"Ação": "Chat", "Usado": usage["chat"], "Limite": limits["chat"]},
            {"Ação": "Auditoria estruturada", "Usado": usage["structured_audit"], "Limite": limits["structured_audit"]},
            {"Ação": "Relatório", "Usado": usage["report"], "Limite": limits["report"]},
            {"Ação": "Matriz", "Usado": usage["matrix"], "Limite": limits["matrix"]},
            {"Ação": "Aprofundamento", "Usado": usage["deep_dive"], "Limite": limits["deep_dive"]},
            {"Ação": "Auditoria completa", "Usado": usage["full_audit"], "Limite": limits["full_audit"]},
        ])
        st.dataframe(usage_df, use_container_width=True, hide_index=True)

# =========================================================
# DOCX / PDF
# =========================================================

def docx_from_text(title: str, text: str) -> bytes:
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    h = doc.add_paragraph()
    run = h.add_run(safe_str(title))
    run.bold = True
    run.font.size = Pt(16)

    doc.add_paragraph("")

    for line in flatten_markdown_to_lines(text):
        stripped = sanitize_xml_text(line).strip()

        if not stripped:
            doc.add_paragraph("")
            continue

        if stripped.startswith("# "):
            p = doc.add_paragraph()
            r = p.add_run(sanitize_xml_text(stripped[2:].strip()))
            r.bold = True
            r.font.size = Pt(15)
        elif stripped.startswith("## "):
            p = doc.add_paragraph()
            r = p.add_run(sanitize_xml_text(stripped[3:].strip()))
            r.bold = True
            r.font.size = Pt(13)
        elif stripped.startswith("### "):
            p = doc.add_paragraph()
            r = p.add_run(sanitize_xml_text(stripped[4:].strip()))
            r.bold = True
            r.font.size = Pt(11.5)
        elif stripped.startswith("- "):
            doc.add_paragraph(sanitize_xml_text(stripped[2:].strip()), style="List Bullet")
        else:
            doc.add_paragraph(sanitize_xml_text(stripped))

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()


def pdf_from_text(title: str, text: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 50
    right = 50
    top = height - 50
    bottom = 50
    usable_width = width - left - right
    y = top

    def new_page():
        nonlocal y
        c.showPage()
        y = top

    def wrap_line(line: str, font_name: str, font_size: int) -> List[str]:
        words = line.split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            test = current + " " + word
            if stringWidth(test, font_name, font_size) <= usable_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    c.setTitle(safe_str(title))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, y, safe_str(title))
    y -= 28

    for raw_line in flatten_markdown_to_lines(text):
        if y < bottom + 30:
            new_page()

        line = sanitize_xml_text(raw_line).strip()

        if not line:
            y -= 10
            continue

        if line.startswith("# "):
            c.setFont("Helvetica-Bold", 15)
            chunks = wrap_line(line[2:].strip(), "Helvetica-Bold", 15)
            for ch in chunks:
                if y < bottom + 25:
                    new_page()
                c.drawString(left, y, sanitize_xml_text(ch))
                y -= 20
        elif line.startswith("## "):
            c.setFont("Helvetica-Bold", 13)
            chunks = wrap_line(line[3:].strip(), "Helvetica-Bold", 13)
            for ch in chunks:
                if y < bottom + 22:
                    new_page()
                c.drawString(left, y, sanitize_xml_text(ch))
                y -= 18
        elif line.startswith("### "):
            c.setFont("Helvetica-Bold", 11)
            chunks = wrap_line(line[4:].strip(), "Helvetica-Bold", 11)
            for ch in chunks:
                if y < bottom + 20:
                    new_page()
                c.drawString(left, y, sanitize_xml_text(ch))
                y -= 16
        elif line.startswith("- "):
            c.setFont("Helvetica", 10)
            bullet_text = "• " + line[2:].strip()
            chunks = wrap_line(bullet_text, "Helvetica", 10)
            for ch in chunks:
                if y < bottom + 18:
                    new_page()
                c.drawString(left + 8, y, sanitize_xml_text(ch))
                y -= 14
        else:
            c.setFont("Helvetica", 10)
            chunks = wrap_line(line, "Helvetica", 10)
            for ch in chunks:
                if y < bottom + 18:
                    new_page()
                c.drawString(left, y, sanitize_xml_text(ch))
                y -= 14

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def matrix_to_docx_bytes(df: pd.DataFrame, title: str) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    p = doc.add_paragraph()
    r = p.add_run(safe_str(title))
    r.bold = True
    r.font.size = Pt(15)

    doc.add_paragraph("")

    if df.empty:
        doc.add_paragraph("Nenhum item de matriz de conformidade foi gerado.")
    else:
        cols = list(df.columns)
        table = doc.add_table(rows=1, cols=len(cols))
        table.style = "Table Grid"

        hdr = table.rows[0].cells
        for i, col in enumerate(cols):
            hdr[i].text = safe_str(col)

        for _, row in df.iterrows():
            cells = table.add_row().cells
            for i, col in enumerate(cols):
                cells[i].text = safe_str(row.get(col, ""))

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()


def matrix_to_pdf_bytes(df: pd.DataFrame, title: str) -> bytes:
    text = [f"# {safe_str(title)}", ""]
    if df.empty:
        text.append("Nenhum item de matriz de conformidade foi gerado.")
    else:
        for i, row in df.iterrows():
            text.append(f"## Item {i+1}")
            for col in df.columns:
                text.append(f"- {safe_str(col)}: {safe_str(row.get(col, ''))}")
            text.append("")
    return pdf_from_text(title, "\n".join(text))

# =========================================================
# AUTH GATE
# =========================================================

current_user = get_user_info()

if AUTH_REQUIRED:
    current_user = render_login_gate()

current_role = get_user_role(current_user["email"])

if current_role == "blocked":
    render_access_denied(current_user["email"])

if db_is_configured():
    sync_user_to_db(current_user, current_role)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.subheader("Modo da IA")

    app_mode = st.radio(
        "Modo de operação",
        [
            "Chat técnico",
            "Auditoria completa Isometric",
        ],
        index=0
    )

    st.divider()

    st.write("Bases consultadas:")
    st.write("• PRJ_Nova_Esperanca")
    st.write("• Isometric_Methodology")
    st.write(f"**Modelo:** `{MODEL_NAME}`")

    st.divider()

    show_sources = st.checkbox("Mostrar fontes utilizadas", value=True)
    show_snippets = st.checkbox("Mostrar trechos recuperados", value=True)
    show_attributes = st.checkbox("Mostrar atributos técnicos", value=False)
    show_raw_json = st.checkbox("Mostrar JSON bruto", value=False)

    st.divider()

    st.write("**Precisão fixa:** máxima")
    st.write(f"Projeto: {PROJECT_MAX_RESULTS} trechos")
    st.write(f"Metodologia: {METHODOLOGY_MAX_RESULTS} trechos")

    st.divider()

    st.write("**Logo configurada:**")
    st.code(LOGO_PATH)

    if st.button("Limpar conversa / sessão"):
        for key, value in DEFAULT_STATE.items():
            st.session_state[key] = value
        st.rerun()

render_usage_overview_in_sidebar(current_user, current_role)

# =========================================================
# API CALLS
# =========================================================

def call_file_search_for_store(
    messages: List[Dict[str, str]],
    vector_store_id: str,
    max_results: int,
    extra_system_prompt: Optional[str] = None,
):
    system_text = SYSTEM_PROMPT
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


def call_reasoning_over_context(user_content: str, extra_system_prompt: Optional[str] = None):
    system_text = SYSTEM_PROMPT
    if extra_system_prompt:
        system_text += "\n\n" + extra_system_prompt

    return client.responses.create(
        model=MODEL_NAME,
        input=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )


def build_combined_context_prompt(
    user_question: str,
    project_sources: List[Dict[str, Any]],
    methodology_sources: List[Dict[str, Any]],
    output_mode: str = "answer"
) -> str:
    project_block = []
    for i, src in enumerate(project_sources, start=1):
        project_block.append(
            f"[PROJETO {i}] Documento: {safe_str(src['filename'])} | Página/Seção: {safe_str(src.get('page') or 'não identificada')}\nTrecho:\n{sanitize_xml_text(src.get('text') or '')}\n"
        )

    methodology_block = []
    for i, src in enumerate(methodology_sources, start=1):
        methodology_block.append(
            f"[METODOLOGIA {i}] Documento: {safe_str(src['filename'])} | Página/Seção: {safe_str(src.get('page') or 'não identificada')}\nTrecho:\n{sanitize_xml_text(src.get('text') or '')}\n"
        )

    instruction_by_mode = {
        "answer": """
Responda à pergunta do usuário usando EXCLUSIVAMENTE os trechos abaixo.
Compare explicitamente Projeto × Metodologia quando aplicável.
Não use conhecimento externo.
Siga o formato obrigatório definido no system prompt.
""",
        "audit_json": """
Produza uma auditoria estruturada em JSON VÁLIDO.
Use EXCLUSIVAMENTE os trechos abaixo.
Não use conhecimento externo.
""",
        "report": """
Produza um relatório consolidado de auditoria.
Use EXCLUSIVAMENTE os trechos abaixo.
Não use conhecimento externo.
""",
        "matrix": """
Produza uma matriz de conformidade em JSON VÁLIDO.
Use EXCLUSIVAMENTE os trechos abaixo.
Não use conhecimento externo.
""",
    }

    return sanitize_xml_text(f"""
Pergunta do usuário:
{safe_str(user_question)}

{instruction_by_mode[output_mode]}

======================
TRECHOS DO PROJETO
======================
{chr(10).join(project_block) if project_block else "Nenhum trecho de projeto recuperado."}

======================
TRECHOS DA METODOLOGIA
======================
{chr(10).join(methodology_block) if methodology_block else "Nenhum trecho metodológico recuperado."}
""")


def build_deep_dive_prompt(
    selected_item: str,
    user_question: str,
    project_sources: List[Dict[str, Any]],
    methodology_sources: List[Dict[str, Any]],
    audit_json: Optional[Dict[str, Any]],
    matrix_json: Optional[Dict[str, Any]],
) -> str:
    base = build_combined_context_prompt(
        user_question=user_question,
        project_sources=project_sources,
        methodology_sources=methodology_sources,
        output_mode="report"
    )

    extra = f"""

ITEM SELECIONADO PARA APROFUNDAMENTO:
{safe_str(selected_item)}
"""

    if audit_json:
        extra += "\nAUDITORIA JSON DISPONÍVEL:\n"
        extra += sanitize_xml_text(json.dumps(audit_json, ensure_ascii=False, indent=2))

    if matrix_json:
        extra += "\n\nMATRIZ DE CONFORMIDADE DISPONÍVEL:\n"
        extra += sanitize_xml_text(json.dumps(matrix_json, ensure_ascii=False, indent=2))

    return sanitize_xml_text(base + "\n\n" + extra)

# =========================================================
# CHAT TÉCNICO MODE
# =========================================================

def render_chat_mode():
    project_name = "Projeto Nova Esperança"
    st.session_state["current_project_name"] = project_name

    if db_is_configured():
        ensure_project_record(current_user["email"], project_name)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Faça uma pergunta sobre o projeto ou solicite uma análise documental...")

    if user_input:
        if not can_consume(current_user["email"], current_role, "chat"):
            st.error("Limite de uso do chat atingido para o período atual.")
            return

        consume_usage(current_user["email"], "chat", project_name)

        st.session_state.messages.append({"role": "user", "content": sanitize_xml_text(user_input)})
        st.session_state.last_user_question = sanitize_xml_text(user_input)

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Executando busca documental de máxima precisão..."):
                try:
                    project_search_response = call_file_search_for_store(
                        messages=st.session_state.messages,
                        vector_store_id=PROJECT_VECTOR_STORE_ID,
                        max_results=PROJECT_MAX_RESULTS,
                        extra_system_prompt="Recupere evidências da documentação do projeto relevantes para a pergunta."
                    )
                    project_sources = extract_file_search_results(project_search_response, "Projeto")

                    methodology_search_response = call_file_search_for_store(
                        messages=st.session_state.messages,
                        vector_store_id=METHODOLOGY_VECTOR_STORE_ID,
                        max_results=METHODOLOGY_MAX_RESULTS,
                        extra_system_prompt="Recupere requisitos metodológicos relevantes para a pergunta."
                    )
                    methodology_sources = extract_file_search_results(methodology_search_response, "Metodologia")

                    all_sources = deduplicate_sources(project_sources + methodology_sources)

                    combined_prompt = build_combined_context_prompt(
                        user_question=user_input,
                        project_sources=project_sources,
                        methodology_sources=methodology_sources,
                        output_mode="answer"
                    )

                    answer_response = call_reasoning_over_context(user_content=combined_prompt)
                    answer_text = get_response_text(answer_response).strip()

                    if not answer_text:
                        answer_text = "A base de conhecimento não contém informação suficiente para responder com segurança."

                    answer_text = sanitize_xml_text(answer_text)
                    st.markdown(answer_text)

                    if show_sources:
                        st.markdown("---")
                        render_sources_block("Fontes do Projeto", project_sources, show_attributes, show_snippets)
                        render_sources_block("Fontes da Metodologia", methodology_sources, show_attributes, show_snippets)

                    st.session_state.last_answer_text = answer_text
                    st.session_state.last_sources_project = project_sources
                    st.session_state.last_sources_methodology = methodology_sources
                    st.session_state.last_sources_all = all_sources
                    st.session_state.last_audit_json = None
                    st.session_state.last_report_text = ""
                    st.session_state.last_compliance_matrix_json = None
                    st.session_state.last_deep_dive_text = ""

                    final_answer_for_history = answer_text

                except Exception as e:
                    final_answer_for_history = f"Erro ao consultar a {APP_NAME}: {str(e)}"
                    st.error(final_answer_for_history)
                    st.session_state.last_answer_text = final_answer_for_history
                    st.session_state.last_sources_project = []
                    st.session_state.last_sources_methodology = []
                    st.session_state.last_sources_all = []
                    st.session_state.last_audit_json = None
                    st.session_state.last_report_text = ""
                    st.session_state.last_compliance_matrix_json = None
                    st.session_state.last_deep_dive_text = ""

        st.session_state.messages.append({"role": "assistant", "content": sanitize_xml_text(final_answer_for_history)})

    st.markdown("---")
    st.subheader("Ações de auditoria")

    has_question = bool(st.session_state.last_user_question)

    if not has_question:
        st.info("Envie uma pergunta no chat para habilitar as ações de auditoria.")

    can_audit = has_question and can_consume(current_user["email"], current_role, "structured_audit")
    can_report = has_question and can_consume(current_user["email"], current_role, "report")
    can_matrix = has_question and can_consume(current_user["email"], current_role, "matrix")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        generate_audit = st.button("Gerar auditoria estruturada", use_container_width=True, disabled=not can_audit)
    with col_b:
        generate_report = st.button("Gerar relatório consolidado", use_container_width=True, disabled=not can_report)
    with col_c:
        generate_matrix = st.button("Gerar matriz de conformidade", use_container_width=True, disabled=not can_matrix)

    if generate_audit:
        consume_usage(current_user["email"], "structured_audit", project_name)
        with st.spinner("Gerando auditoria estruturada..."):
            try:
                audit_prompt = build_combined_context_prompt(
                    user_question=st.session_state.last_user_question,
                    project_sources=st.session_state.last_sources_project,
                    methodology_sources=st.session_state.last_sources_methodology,
                    output_mode="audit_json"
                )
                audit_response = call_reasoning_over_context(user_content=audit_prompt, extra_system_prompt=JSON_AUDIT_PROMPT)
                audit_text = get_response_text(audit_response).strip()
                audit_json = try_parse_json(audit_text)

                if audit_json:
                    st.session_state.last_audit_json = audit_json
                else:
                    st.error("Não foi possível converter a auditoria em JSON válido.")
            except Exception as e:
                st.error(f"Erro ao gerar auditoria estruturada: {str(e)}")

    if st.session_state.last_audit_json:
        st.markdown("---")
        st.markdown("## Auditoria estruturada")
        st.markdown(render_audit_json(st.session_state.last_audit_json))

        if show_raw_json:
            st.markdown("### JSON da auditoria")
            st.json(st.session_state.last_audit_json)

    if generate_report:
        consume_usage(current_user["email"], "report", project_name)
        with st.spinner("Gerando relatório consolidado..."):
            try:
                report_prompt = build_combined_context_prompt(
                    user_question=st.session_state.last_user_question,
                    project_sources=st.session_state.last_sources_project,
                    methodology_sources=st.session_state.last_sources_methodology,
                    output_mode="report"
                )

                if st.session_state.last_audit_json:
                    report_prompt += "\n\nAUDITORIA JSON JÁ PRODUZIDA:\n"
                    report_prompt += sanitize_xml_text(json.dumps(st.session_state.last_audit_json, ensure_ascii=False, indent=2))

                report_response = call_reasoning_over_context(user_content=report_prompt, extra_system_prompt=REPORT_PROMPT)
                report_text = get_response_text(report_response).strip()

                if not report_text:
                    report_text = "A base de conhecimento não contém informação suficiente para responder com segurança."

                st.session_state.last_report_text = sanitize_xml_text(report_text)
            except Exception as e:
                st.error(f"Erro ao gerar relatório consolidado: {str(e)}")

    if st.session_state.last_report_text:
        st.markdown("---")
        st.markdown("## Relatório consolidado")
        st.markdown(st.session_state.last_report_text)

    if generate_matrix:
        consume_usage(current_user["email"], "matrix", project_name)
        with st.spinner("Gerando matriz de conformidade..."):
            try:
                matrix_prompt = build_combined_context_prompt(
                    user_question=st.session_state.last_user_question,
                    project_sources=st.session_state.last_sources_project,
                    methodology_sources=st.session_state.last_sources_methodology,
                    output_mode="matrix"
                )

                matrix_response = call_reasoning_over_context(user_content=matrix_prompt, extra_system_prompt=COMPLIANCE_MATRIX_PROMPT)
                matrix_text = get_response_text(matrix_response).strip()
                matrix_json = try_parse_json(matrix_text)

                if matrix_json:
                    st.session_state.last_compliance_matrix_json = matrix_json
                else:
                    st.error("Não foi possível converter a matriz de conformidade em JSON válido.")
            except Exception as e:
                st.error(f"Erro ao gerar matriz de conformidade: {str(e)}")

    matrix_df = pd.DataFrame()

    if st.session_state.last_compliance_matrix_json:
        st.markdown("---")
        st.markdown("## Matriz de conformidade")
        matrix_df = matrix_json_to_dataframe(st.session_state.last_compliance_matrix_json)
        st.dataframe(matrix_df, use_container_width=True, hide_index=True)

        if show_raw_json:
            st.markdown("### JSON da matriz")
            st.json(st.session_state.last_compliance_matrix_json)

    st.markdown("---")
    st.subheader("Aprofundamento de não conformidade")

    deep_dive_candidates = []

    if st.session_state.last_audit_json:
        for item in st.session_state.last_audit_json.get("potenciais_nao_conformidades", []) or []:
            deep_dive_candidates.append(f"[Potencial não conformidade] {safe_str(item)}")
        for item in st.session_state.last_audit_json.get("lacunas_documentais", []) or []:
            deep_dive_candidates.append(f"[Lacuna documental] {safe_str(item)}")
        for item in st.session_state.last_audit_json.get("inconsistencias_documentais", []) or []:
            deep_dive_candidates.append(f"[Inconsistência] {safe_str(item)}")

    if not matrix_df.empty:
        for _, row in matrix_df.iterrows():
            status = safe_str(row.get("status", ""))
            if status in {"atende_parcialmente", "nao_identificado", "potencial_nao_conformidade", "inconsistencia"}:
                deep_dive_candidates.append(
                    f"[Matriz | {status}] Requisito: {safe_str(row.get('requisito', ''))} | Recomendação: {safe_str(row.get('recomendacao', ''))}"
                )

    deep_dive_candidates = list(dict.fromkeys(deep_dive_candidates))

    if deep_dive_candidates:
        selected_issue = st.selectbox("Selecione o item para aprofundamento", options=deep_dive_candidates)

        generate_deep_dive = st.button(
            "Aprofundar item selecionado",
            use_container_width=False,
            disabled=not can_consume(current_user["email"], current_role, "deep_dive")
        )

        if generate_deep_dive:
            consume_usage(current_user["email"], "deep_dive", project_name)
            with st.spinner("Aprofundando item selecionado..."):
                try:
                    deep_prompt = build_deep_dive_prompt(
                        selected_item=selected_issue,
                        user_question=st.session_state.last_user_question,
                        project_sources=st.session_state.last_sources_project,
                        methodology_sources=st.session_state.last_sources_methodology,
                        audit_json=st.session_state.last_audit_json,
                        matrix_json=st.session_state.last_compliance_matrix_json,
                    )

                    deep_response = call_reasoning_over_context(user_content=deep_prompt, extra_system_prompt=DEEP_DIVE_PROMPT)
                    deep_text = get_response_text(deep_response).strip()

                    if not deep_text:
                        deep_text = "A base de conhecimento não contém informação suficiente para responder com segurança."

                    st.session_state.last_deep_dive_text = sanitize_xml_text(deep_text)
                except Exception as e:
                    st.error(f"Erro ao aprofundar item: {str(e)}")
    else:
        st.info("Gere a auditoria estruturada e/ou a matriz de conformidade para habilitar o aprofundamento.")

    if st.session_state.last_deep_dive_text:
        st.markdown("## Aprofundamento técnico")
        st.markdown(st.session_state.last_deep_dive_text)

# =========================================================
# FULL AUDIT MODE
# =========================================================

def render_full_audit_mode():
    st.subheader("Auditoria completa da metodologia Isometric")
    st.caption("Agora com duas saídas: auditoria resumida e dossiê de elegibilidade completo.")

    all_modules = sorted(list({r["module"] for r in ISOMETRIC_REQUIREMENTS}))

    with st.expander("Configuração da auditoria", expanded=True):
        project_name = st.text_input("Nome do projeto", value=st.session_state.get("current_project_name", "Projeto Nova Esperança"))
        selected_modules = st.multiselect("Módulos a auditar", options=all_modules, default=all_modules)
        show_trails = st.checkbox("Exibir trilha de auditoria detalhada", value=False, key="show_trails_full_audit")

    st.session_state["current_project_name"] = project_name

    if db_is_configured():
        ensure_project_record(current_user["email"], project_name)

    if st.button(
        "Executar auditoria completa",
        type="primary",
        use_container_width=True,
        disabled=not can_consume(current_user["email"], current_role, "full_audit")
    ):
        consume_usage(current_user["email"], "full_audit", project_name)
        with st.spinner("Executando auditoria requisito por requisito..."):
            try:
                engine = AuditEngine(
                    api_key=OPENAI_API_KEY,
                    model=MODEL_NAME,
                    project_vector_store_id=PROJECT_VECTOR_STORE_ID,
                    methodology_vector_store_id=METHODOLOGY_VECTOR_STORE_ID,
                    project_name=project_name,
                )

                audit_output = engine.run_full_audit(selected_modules=selected_modules)
                results = audit_output["results"]
                trails = audit_output["trails"]
                summary = engine.summarize_results(results)
                df = build_audit_dataframe(results)

                st.session_state["last_full_audit_results"] = results
                st.session_state["last_full_audit_trails"] = trails
                st.session_state["last_full_audit_summary"] = summary
                st.session_state["last_full_audit_df"] = df
                st.session_state["last_full_audit_run_id"] = audit_output["run_id"]

                st.success("Auditoria concluída com sucesso.")
            except Exception as e:
                st.error(f"Erro ao executar auditoria completa: {str(e)}")

    if isinstance(st.session_state.get("last_full_audit_df"), pd.DataFrame) and not st.session_state["last_full_audit_df"].empty:
        df = st.session_state["last_full_audit_df"]
        summary = st.session_state["last_full_audit_summary"]
        trails = st.session_state["last_full_audit_trails"]
        run_id = st.session_state["last_full_audit_run_id"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Requisitos", summary.get("total_requirements", 0))
        col2.metric("Score geral", f"{summary.get('overall_score', 0)}%")
        col3.metric("Não conformes", summary.get("status_counts", {}).get("Não conforme", 0))
        col4.metric("Não evidenciados", summary.get("status_counts", {}).get("Não evidenciado", 0))

        st.markdown("---")
        st.subheader("Distribuição por status")
        status_df = pd.DataFrame([
            {"Status": k, "Quantidade": v}
            for k, v in (summary.get("status_counts", {}) or {}).items()
        ])
        st.dataframe(status_df, use_container_width=True, hide_index=True)

        st.subheader("Distribuição por risco")
        risk_df = pd.DataFrame([
            {"Risco": k, "Quantidade": v}
            for k, v in (summary.get("risk_counts", {}) or {}).items()
        ])
        st.dataframe(risk_df, use_container_width=True, hide_index=True)

        st.subheader("Score por módulo")
        module_df = pd.DataFrame([
            {"Módulo": k, "Score médio": v}
            for k, v in (summary.get("module_scores", {}) or {}).items()
        ])
        if not module_df.empty:
            module_df = module_df.sort_values("Score médio", ascending=False)
        st.dataframe(module_df, use_container_width=True, hide_index=True)

        st.subheader("Matriz de conformidade")
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv_bytes = convert_df_to_csv_bytes(df)
        json_payload = {
            "run_id": run_id,
            "summary": summary,
            "results": st.session_state["last_full_audit_results"],
            "trails": st.session_state["last_full_audit_trails"],
        }
        json_bytes = convert_json_to_bytes(json_payload)

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

        st.markdown("---")
        st.subheader("Downloads da auditoria")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "Auditoria resumida (.md)",
                data=full_audit_text,
                file_name=f"auditoria_resumida_isometric_{run_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with c2:
            st.download_button(
                "Auditoria resumida (.docx)",
                data=full_audit_docx,
                file_name=f"auditoria_resumida_isometric_{run_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with c3:
            st.download_button(
                "Auditoria resumida (.pdf)",
                data=full_audit_pdf,
                file_name=f"auditoria_resumida_isometric_{run_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        c4, c5, c6 = st.columns(3)
        with c4:
            st.download_button(
                "Dossiê de elegibilidade (.md)",
                data=eligibility_dossier_text,
                file_name=f"dossie_elegibilidade_{run_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with c5:
            st.download_button(
                "Dossiê de elegibilidade (.docx)",
                data=eligibility_docx,
                file_name=f"dossie_elegibilidade_{run_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with c6:
            st.download_button(
                "Dossiê de elegibilidade (.pdf)",
                data=eligibility_pdf,
                file_name=f"dossie_elegibilidade_{run_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        c7, c8, c9, c10 = st.columns(4)
        with c7:
            st.download_button(
                "Matriz (.csv)",
                data=csv_bytes,
                file_name=f"matriz_conformidade_isometric_{run_id}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c8:
            st.download_button(
                "Matriz (.docx)",
                data=matrix_docx,
                file_name=f"matriz_conformidade_isometric_{run_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with c9:
            st.download_button(
                "Matriz (.pdf)",
                data=matrix_pdf,
                file_name=f"matriz_conformidade_isometric_{run_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with c10:
            st.download_button(
                "Trilha / auditoria (.json)",
                data=json_bytes,
                file_name=f"auditoria_isometric_{run_id}.json",
                mime="application/json",
                use_container_width=True
            )

        if show_trails:
            st.markdown("---")
            st.subheader("Trilha de auditoria detalhada")
            for i, trail in enumerate(trails, start=1):
                with st.expander(f"[{i}] {trail.get('requirement_id')} — {trail.get('title')}"):
                    st.markdown("**Query do projeto**")
                    st.code(trail.get("project_query", ""), language="text")

                    st.markdown("**Query da metodologia**")
                    st.code(trail.get("methodology_query", ""), language="text")

                    st.markdown("**Trechos recuperados do projeto**")
                    st.code(trail.get("project_context", ""), language="text")

                    st.markdown("**Trechos recuperados da metodologia**")
                    st.code(trail.get("methodology_context", ""), language="text")

                    st.markdown("**Resposta bruta do modelo**")
                    st.code(trail.get("model_response_raw", ""), language="json")

                    st.markdown("**Resultado interpretado**")
                    st.json(trail.get("parsed_result", {}))
    else:
        st.info("Execute a auditoria completa para gerar a matriz de conformidade.")

# =========================================================
# ROUTER
# =========================================================

if app_mode == "Chat técnico":
    render_chat_mode()
else:
    render_full_audit_mode()
