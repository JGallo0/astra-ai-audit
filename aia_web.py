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

# =========================================================
# CONFIG
# =========================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1")

PROJECT_VECTOR_STORE_ID = os.getenv(
    "PROJECT_VECTOR_STORE_ID",
    "vs_69b4035175c48191ae87cbfcf0663248"
)

METHODOLOGY_VECTOR_STORE_ID = os.getenv(
    "METHODOLOGY_VECTOR_STORE_ID",
    "vs_69b310b246c08191a7eb5b13c1977787"
)

# Pode ser .jpg ou .png
LOGO_PATH = os.getenv("ASTRACARBON_LOGO_PATH", "assets/logo_astracarbon.jpg")

# Máxima precisão fixa
PROJECT_MAX_RESULTS = 12
METHODOLOGY_MAX_RESULTS = 12

SYSTEM_PROMPT = """
Você é a AiA, auditora técnica da AstraCarbon especializada em projetos de remoção de carbono via biochar.

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
    page_title="AiA — AstraCarbon",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 AiA — AstraCarbon Auditor")
st.caption("Auditor técnico documental de projetos de biochar e créditos de carbono")

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
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.subheader("Modo da IA")
    st.write("Auditoria metodológica")
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

    if st.button("Limpar conversa"):
        for key, value in DEFAULT_STATE.items():
            st.session_state[key] = value
        st.rerun()

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


def render_sources_block(title: str, sources: List[Dict[str, Any]]):
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

# =========================================================
# DOCX / PDF SIMPLE EXPORTS
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
# PROFESSIONAL DOCX EXPORT
# =========================================================

def set_document_margins(section, top=2.2, bottom=2.0, left=2.2, right=2.0):
    section.top_margin = Cm(top)
    section.bottom_margin = Cm(bottom)
    section.left_margin = Cm(left)
    section.right_margin = Cm(right)


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    run = p.add_run("Página ")
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._r.append(fld)


def add_paragraph_md(doc, line: str):
    stripped = sanitize_xml_text(line).strip()

    if not stripped:
        doc.add_paragraph("")
        return

    if stripped.startswith("# "):
        p = doc.add_paragraph()
        p.style = "Heading 1"
        p.add_run(sanitize_xml_text(stripped[2:].strip()))
        return

    if stripped.startswith("## "):
        p = doc.add_paragraph()
        p.style = "Heading 2"
        p.add_run(sanitize_xml_text(stripped[3:].strip()))
        return

    if stripped.startswith("### "):
        p = doc.add_paragraph()
        p.style = "Heading 3"
        p.add_run(sanitize_xml_text(stripped[4:].strip()))
        return

    if stripped.startswith("- "):
        doc.add_paragraph(sanitize_xml_text(stripped[2:].strip()), style="List Bullet")
        return

    doc.add_paragraph(sanitize_xml_text(stripped))


def add_logo_and_cover(doc, logo_path: str, question: str):
    section = doc.sections[0]
    set_document_margins(section)

    doc.add_paragraph("")

    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_logo = p_logo.add_run()
        run_logo.add_picture(logo_path, width=Inches(3.4))

    doc.add_paragraph("")

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_title.add_run("Dossiê de Auditoria Metodológica")
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = RGBColor(14, 47, 94)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p_sub.add_run("AiA — AstraCarbon Inteligência Artificial")
    r2.bold = True
    r2.font.size = Pt(13)
    r2.font.color.rgb = RGBColor(8, 90, 214)

    doc.add_paragraph("")

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run("Projeto: Biochar / Auditoria Documental\n").bold = True
    meta.add_run(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    meta.add_run("Base consultada: documentação interna do projeto + documentação metodológica\n")
    meta.add_run("Uso: pré-auditoria, diagnóstico documental e apoio à conformidade metodológica")

    doc.add_paragraph("")
    doc.add_paragraph("")

    p_q = doc.add_paragraph()
    p_q.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rq1 = p_q.add_run("Pergunta auditada\n")
    rq1.bold = True
    rq1.font.size = Pt(12)
    rq2 = p_q.add_run(safe_str(question or "Não identificada"))
    rq2.font.size = Pt(11)

    doc.add_page_break()


def add_identification_table(doc, question: str):
    doc.add_paragraph("1. Identificação da análise", style="Heading 1")

    table = doc.add_table(rows=5, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    rows = [
        ("Ferramenta", "AiA — AstraCarbon Inteligência Artificial"),
        ("Tipo de análise", "Auditoria documental metodológica"),
        ("Escopo", "Projeto × Metodologia"),
        ("Data/hora", datetime.now().strftime("%d/%m/%Y %H:%M")),
        ("Pergunta auditada", safe_str(question or "Não identificada")),
    ]

    for i, (k, v) in enumerate(rows):
        table.cell(i, 0).text = safe_str(k)
        table.cell(i, 1).text = safe_str(v)
        set_cell_shading(table.cell(i, 0), "D9EAF7")

    doc.add_paragraph("")


def add_audit_summary_table(doc, audit_json: Optional[Dict[str, Any]]):
    doc.add_paragraph("2. Sumário executivo da auditoria", style="Heading 1")

    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr = table.rows[0].cells
    hdr[0].text = "Campo"
    hdr[1].text = "Síntese"
    set_cell_shading(hdr[0], "0E2F5E")
    set_cell_shading(hdr[1], "0E2F5E")

    for cell in hdr:
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.bold = True

    if audit_json:
        rows = [
            ("Nível de risco", safe_str(audit_json.get("nivel_risco", "não identificado"))),
            ("Qtd. lacunas documentais", safe_str(len(audit_json.get("lacunas_documentais", []) or []))),
            ("Qtd. inconsistências", safe_str(len(audit_json.get("inconsistencias_documentais", []) or []))),
            ("Qtd. potenciais não conformidades", safe_str(len(audit_json.get("potenciais_nao_conformidades", []) or []))),
            ("Qtd. recomendações", safe_str(len(audit_json.get("recomendacoes_tecnicas", []) or []))),
        ]
    else:
        rows = [
            ("Nível de risco", "não identificado"),
            ("Qtd. lacunas documentais", "0"),
            ("Qtd. inconsistências", "0"),
            ("Qtd. potenciais não conformidades", "0"),
            ("Qtd. recomendações", "0"),
        ]

    for k, v in rows:
        row = table.add_row().cells
        row[0].text = safe_str(k)
        row[1].text = safe_str(v)
        set_cell_shading(row[0], "EAF3F9")

    doc.add_paragraph("")


def add_matrix_table(doc, matrix_json: Optional[Dict[str, Any]]):
    doc.add_paragraph("7. Matriz de conformidade", style="Heading 1")

    df = matrix_json_to_dataframe(matrix_json)

    if df.empty:
        doc.add_paragraph("Nenhum item de matriz de conformidade foi gerado.")
        return

    cols = [
        "requisito",
        "status",
        "risco",
        "documento_metodologia",
        "documento_projeto",
        "recomendacao",
    ]

    df = df[[c for c in cols if c in df.columns]]

    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr = table.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr[i].text = safe_str(col)
        set_cell_shading(hdr[i], "0E2F5E")
        for p in hdr[i].paragraphs:
            for run in p.runs:
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.bold = True

    for _, row_data in df.iterrows():
        row = table.add_row().cells
        for i, col in enumerate(df.columns):
            row[i].text = safe_str(row_data.get(col, ""))

    doc.add_paragraph("")


def add_sources_appendix(doc, sources: List[Dict[str, Any]]):
    doc.add_paragraph("9. Fontes utilizadas", style="Heading 1")

    if not sources:
        doc.add_paragraph("Nenhuma fonte registrada.")
        return

    for src in sources:
        filename = safe_str(src.get("filename", "Documento sem nome"))
        source_group = safe_str(src.get("source_group", ""))
        page = safe_str(src.get("page") or "não identificada")
        score = safe_str(src.get("score"))
        trecho = sanitize_xml_text((src.get("text") or "").strip())

        p = doc.add_paragraph(style="List Number")
        r = p.add_run(filename)
        r.bold = True

        meta = doc.add_paragraph()
        meta.add_run("Grupo: ").bold = True
        meta.add_run(source_group)
        meta.add_run(" | Página/Seção: ").bold = True
        meta.add_run(page)
        meta.add_run(" | Score: ").bold = True
        meta.add_run(score)

        if trecho:
            doc.add_paragraph("Trecho recuperado:")
            for line in flatten_markdown_to_lines(trecho):
                clean_line = sanitize_xml_text(line)
                if clean_line.strip():
                    doc.add_paragraph(clean_line)

        doc.add_paragraph("")


def build_professional_audit_docx(
    question: str,
    answer_text: str,
    audit_json: Optional[Dict[str, Any]],
    report_text: str,
    matrix_json: Optional[Dict[str, Any]],
    deep_dive_text: str,
    sources: List[Dict[str, Any]],
    logo_path: str
) -> bytes:
    doc = Document()

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)

    for section in doc.sections:
        set_document_margins(section)
        set_page_number_footer(section)

    add_logo_and_cover(doc, logo_path, safe_str(question))
    add_identification_table(doc, safe_str(question))
    add_audit_summary_table(doc, audit_json)

    doc.add_paragraph("3. Resposta técnica da AiA", style="Heading 1")
    if answer_text:
        for line in flatten_markdown_to_lines(sanitize_xml_text(answer_text)):
            add_paragraph_md(doc, line)
    else:
        doc.add_paragraph("Não disponível.")

    doc.add_paragraph("4. Auditoria estruturada", style="Heading 1")
    if audit_json:
        audit_md = sanitize_xml_text(render_audit_json(audit_json))
        for line in flatten_markdown_to_lines(audit_md):
            add_paragraph_md(doc, line)
    else:
        doc.add_paragraph("Auditoria estruturada não gerada.")

    doc.add_paragraph("5. Relatório consolidado", style="Heading 1")
    if report_text:
        for line in flatten_markdown_to_lines(sanitize_xml_text(report_text)):
            add_paragraph_md(doc, line)
    else:
        doc.add_paragraph("Relatório consolidado não gerado.")

    doc.add_paragraph("6. Aprofundamento técnico", style="Heading 1")
    if deep_dive_text:
        for line in flatten_markdown_to_lines(sanitize_xml_text(deep_dive_text)):
            add_paragraph_md(doc, line)
    else:
        doc.add_paragraph("Aprofundamento técnico não gerado.")

    add_matrix_table(doc, matrix_json)
    add_sources_appendix(doc, sources)

    doc.add_paragraph("10. Observação metodológica", style="Heading 1")
    doc.add_paragraph(
        sanitize_xml_text(
            "Este documento foi gerado pela AiA com base exclusivamente na documentação interna recuperada "
            "na base do projeto e na base metodológica. Ausência de evidência documental não deve ser "
            "interpretada automaticamente como descumprimento definitivo, mas como lacuna a ser confirmada."
        )
    )

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

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
# CHAT HISTORY
# =========================================================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================================================
# USER INPUT
# =========================================================

user_input = st.chat_input("Faça uma pergunta sobre o projeto ou solicite uma análise documental...")

if user_input:
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
                    render_sources_block("Fontes do Projeto", project_sources)
                    render_sources_block("Fontes da Metodologia", methodology_sources)

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
                final_answer_for_history = f"Erro ao consultar a AiA: {str(e)}"
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

# =========================================================
# ACTIONS
# =========================================================

st.markdown("---")
st.subheader("Ações de auditoria")

has_question = bool(st.session_state.last_user_question)

if not has_question:
    st.info("Envie uma pergunta no chat para habilitar as ações de auditoria.")

col_a, col_b, col_c = st.columns(3)

with col_a:
    generate_audit = st.button(
        "Gerar auditoria estruturada",
        use_container_width=True,
        disabled=not has_question
    )

with col_b:
    generate_report = st.button(
        "Gerar relatório consolidado",
        use_container_width=True,
        disabled=not has_question
    )

with col_c:
    generate_matrix = st.button(
        "Gerar matriz de conformidade",
        use_container_width=True,
        disabled=not has_question
    )

if generate_audit:
    with st.spinner("Gerando auditoria estruturada..."):
        try:
            audit_prompt = build_combined_context_prompt(
                user_question=st.session_state.last_user_question,
                project_sources=st.session_state.last_sources_project,
                methodology_sources=st.session_state.last_sources_methodology,
                output_mode="audit_json"
            )
            audit_response = call_reasoning_over_context(
                user_content=audit_prompt,
                extra_system_prompt=JSON_AUDIT_PROMPT
            )
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

            report_response = call_reasoning_over_context(
                user_content=report_prompt,
                extra_system_prompt=REPORT_PROMPT
            )
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
    with st.spinner("Gerando matriz de conformidade..."):
        try:
            matrix_prompt = build_combined_context_prompt(
                user_question=st.session_state.last_user_question,
                project_sources=st.session_state.last_sources_project,
                methodology_sources=st.session_state.last_sources_methodology,
                output_mode="matrix"
            )

            matrix_response = call_reasoning_over_context(
                user_content=matrix_prompt,
                extra_system_prompt=COMPLIANCE_MATRIX_PROMPT
            )
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

# =========================================================
# DEEP DIVE
# =========================================================

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
    selected_issue = st.selectbox(
        "Selecione o item para aprofundamento",
        options=deep_dive_candidates
    )

    generate_deep_dive = st.button(
        "Aprofundar item selecionado",
        use_container_width=False
    )

    if generate_deep_dive:
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

                deep_response = call_reasoning_over_context(
                    user_content=deep_prompt,
                    extra_system_prompt=DEEP_DIVE_PROMPT
                )
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
# DOWNLOADS
# =========================================================

st.markdown("---")
st.subheader("Dossiê principal")

if (
    st.session_state.last_answer_text
    or st.session_state.last_audit_json
    or st.session_state.last_report_text
    or st.session_state.last_compliance_matrix_json
    or st.session_state.last_deep_dive_text
):
    professional_docx = build_professional_audit_docx(
        question=st.session_state.last_user_question,
        answer_text=st.session_state.last_answer_text,
        audit_json=st.session_state.last_audit_json,
        report_text=st.session_state.last_report_text,
        matrix_json=st.session_state.last_compliance_matrix_json,
        deep_dive_text=st.session_state.last_deep_dive_text,
        sources=st.session_state.last_sources_all,
        logo_path=LOGO_PATH
    )

    st.download_button(
        "Baixar dossiê profissional (.docx)",
        data=professional_docx,
        file_name="aia_dossie_auditoria_astracarbon.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

st.markdown("---")
st.subheader("Downloads auxiliares")

if st.session_state.last_answer_text:
    answer_docx = docx_from_text("Resposta da AiA", st.session_state.last_answer_text)
    answer_pdf = pdf_from_text("Resposta da AiA", st.session_state.last_answer_text)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Resposta (.md)",
            data=st.session_state.last_answer_text,
            file_name="aia_resposta.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Resposta (.docx)",
            data=answer_docx,
            file_name="aia_resposta.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Resposta (.pdf)",
            data=answer_pdf,
            file_name="aia_resposta.pdf",
            mime="application/pdf",
            use_container_width=True
        )

if st.session_state.last_sources_all:
    src_md = export_sources_markdown(st.session_state.last_sources_all)
    src_docx = docx_from_text("Fontes utilizadas", src_md)
    src_pdf = pdf_from_text("Fontes utilizadas", src_md)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Fontes (.md)",
            data=src_md,
            file_name="aia_fontes.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Fontes (.docx)",
            data=src_docx,
            file_name="aia_fontes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Fontes (.pdf)",
            data=src_pdf,
            file_name="aia_fontes.pdf",
            mime="application/pdf",
            use_container_width=True
        )

if st.session_state.last_audit_json:
    audit_md = render_audit_json(st.session_state.last_audit_json)
    audit_docx = docx_from_text("Auditoria estruturada", audit_md)
    audit_pdf = pdf_from_text("Auditoria estruturada", audit_md)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button(
            "Auditoria (.json)",
            data=json.dumps(st.session_state.last_audit_json, ensure_ascii=False, indent=2),
            file_name="aia_auditoria.json",
            mime="application/json",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Auditoria (.md)",
            data=audit_md,
            file_name="aia_auditoria.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Auditoria (.docx)",
            data=audit_docx,
            file_name="aia_auditoria.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c4:
        st.download_button(
            "Auditoria (.pdf)",
            data=audit_pdf,
            file_name="aia_auditoria.pdf",
            mime="application/pdf",
            use_container_width=True
        )

if st.session_state.last_report_text:
    report_docx = docx_from_text("Relatório consolidado", st.session_state.last_report_text)
    report_pdf = pdf_from_text("Relatório consolidado", st.session_state.last_report_text)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Relatório (.md)",
            data=st.session_state.last_report_text,
            file_name="aia_relatorio.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Relatório (.docx)",
            data=report_docx,
            file_name="aia_relatorio.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Relatório (.pdf)",
            data=report_pdf,
            file_name="aia_relatorio.pdf",
            mime="application/pdf",
            use_container_width=True
        )

if st.session_state.last_compliance_matrix_json:
    matrix_df = matrix_json_to_dataframe(st.session_state.last_compliance_matrix_json)
    matrix_docx = matrix_to_docx_bytes(matrix_df, "Matriz de conformidade")
    matrix_pdf = matrix_to_pdf_bytes(matrix_df, "Matriz de conformidade")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Matriz (.json)",
            data=json.dumps(st.session_state.last_compliance_matrix_json, ensure_ascii=False, indent=2),
            file_name="aia_matriz_conformidade.json",
            mime="application/json",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Matriz (.docx)",
            data=matrix_docx,
            file_name="aia_matriz_conformidade.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Matriz (.pdf)",
            data=matrix_pdf,
            file_name="aia_matriz_conformidade.pdf",
            mime="application/pdf",
            use_container_width=True
        )

if st.session_state.last_deep_dive_text:
    deep_docx = docx_from_text("Aprofundamento técnico", st.session_state.last_deep_dive_text)
    deep_pdf = pdf_from_text("Aprofundamento técnico", st.session_state.last_deep_dive_text)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Aprofundamento (.md)",
            data=st.session_state.last_deep_dive_text,
            file_name="aia_aprofundamento.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Aprofundamento (.docx)",
            data=deep_docx,
            file_name="aia_aprofundamento.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Aprofundamento (.pdf)",
            data=deep_pdf,
            file_name="aia_aprofundamento.pdf",
            mime="application/pdf",
            use_container_width=True
        )