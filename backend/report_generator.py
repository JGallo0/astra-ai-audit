"""
CO2mply — Professional PDF Report Generator
ReportLab-based branded compliance matrix.
"""
import io
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable, Image,
)
from reportlab.platypus.flowables import Flowable

# ── Brand colours ──────────────────────────────────────────────────────────────

NAVY        = "#1A3160"
NAVY_LIGHT  = "#EEF2FA"
GREEN       = "#16A34A"
GREEN_BG    = "#F0FDF4"
AMBER       = "#B45309"
AMBER_BG    = "#FFFBEB"
PURPLE      = "#6D28D9"
PURPLE_BG   = "#F5F3FF"
RED         = "#DC2626"
RED_BG      = "#FEF2F2"
GRAY_DARK   = "#4B5563"
GRAY_MID    = "#9CA3AF"
GRAY_BG     = "#F3F4F6"
BORDER      = "#E5E7EB"
TEXT        = "#111827"
TEXT2       = "#6B7280"

def _c(h): return colors.HexColor(h)

PAGE_W, PAGE_H = A4
ML = 1.8 * cm
MR = 1.8 * cm
MT = 2.2 * cm   # after header bar
MB = 1.8 * cm   # above footer

LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "auditoria_logo.png",
)

# ── Status config ──────────────────────────────────────────────────────────────

STATUS = {
    "compliant":                ("Conforme",    GREEN,  GREEN_BG),
    "partial":                  ("Parcial",     AMBER,  AMBER_BG),
    "future_evidence_required": ("Ev. Futura",  PURPLE, PURPLE_BG),
    "non_compliant":            ("Não conforme",RED,    RED_BG),
    "not_applicable":           ("N/A",         GRAY_MID, GRAY_BG),
    "error":                    ("Erro",        GRAY_MID, GRAY_BG),
}

GENERIC = {
    "Maintain current evidence and proceed to validation readiness.",
    "Partial evidence available; some required elements are incomplete.",
    "Core requirement not met or insufficiently evidenced.",
    "Provide missing documentation and strengthen evidence for identified gaps.",
    "Strengthen consistency and completeness of existing evidence.",
    "Establish missing core elements required for compliance.",
    "Correct failed conditions and provide full supporting evidence before validation.",
    "Providencie esta evidência quando o projeto estiver operacional.",
}

def _lbl(s): return STATUS.get(s, ("?", GRAY_MID, GRAY_BG))[0]
def _fg(s):  return STATUS.get(s, ("?", GRAY_MID, GRAY_BG))[1]
def _bg(s):  return STATUS.get(s, ("?", GRAY_MID, GRAY_BG))[2]

def _clean_notes(notes) -> List[str]:
    if isinstance(notes, str):
        # Already joined string — split back and clean
        parts = [n.strip() for n in notes.split("|") if n.strip()]
    elif isinstance(notes, list):
        parts = [str(n).strip() for n in notes if n]
    else:
        return []
    return [
        n for n in parts
        if n
        and not n.startswith("[Protocolo]")
        and "desenvolvimento:" not in n.lower()
        and "operacional:" not in n.lower()
        and n not in GENERIC
    ]

def _score_str(r: dict) -> str:
    s = r.get("requirement_score")
    if r.get("status") == "not_applicable" or s is None:
        return "N/A"
    try:
        return str(int(round(float(s))))
    except Exception:
        return "N/A"

def _score_color(r: dict) -> str:
    s = r.get("requirement_score")
    if s is None: return GRAY_MID
    try:
        v = float(s)
        return GREEN if v >= 85 else AMBER if v >= 60 else RED
    except Exception:
        return GRAY_MID

def _group_by_module(results: List[dict]) -> Dict[str, List[dict]]:
    groups: Dict[str, List[dict]] = {}
    for r in results:
        mod = (r.get("module") or "other").replace("_", " ").title()
        groups.setdefault(mod, []).append(r)
    return groups

# ── Page callbacks ─────────────────────────────────────────────────────────────

def _make_page_cb(project_name: str, date_str: str):
    def cb(canvas, doc):
        canvas.saveState()
        w, h = A4

        # Header bar
        canvas.setFillColor(_c(NAVY))
        canvas.rect(0, h - 1.3*cm, w, 1.3*cm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawString(ML, h - 0.83*cm, "CO2mply")
        canvas.setFont("Helvetica", 7.5)
        canvas.drawRightString(w - MR, h - 0.83*cm, "Carbon Compliance Intelligence")

        # Footer line
        canvas.setStrokeColor(_c(BORDER))
        canvas.setLineWidth(0.5)
        canvas.line(ML, 1.5*cm, w - MR, 1.5*cm)

        # Footer text
        canvas.setFillColor(_c(TEXT2))
        canvas.setFont("Helvetica", 7)
        canvas.drawString(ML, 0.85*cm,
                          f"CO2mply | Auditoria de Conformidade — {project_name}")
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(w - MR, 0.85*cm,
                               f"Página {doc.page}  |  {date_str}")
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(_c(GRAY_MID))
        canvas.drawCentredString(w/2, 0.85*cm, "CONFIDENCIAL")

        canvas.restoreState()

    return cb

# ── Helpers ────────────────────────────────────────────────────────────────────

def _p(text, style): return Paragraph(text, style)

def _style(**kw) -> ParagraphStyle:
    base = dict(fontName="Helvetica", fontSize=9, leading=12,
                textColor=_c(TEXT), spaceAfter=0, spaceBefore=0)
    base.update(kw)
    return ParagraphStyle("s", **base)

# ── Main function ──────────────────────────────────────────────────────────────

def generate_compliance_matrix_pdf(
    results: List[dict],
    score_data: dict,
    audit_mode: str = "development",
    project_name: str = "Projeto",
    methodology: str = "Isometric Biochar",
) -> bytes:

    score      = float(score_data.get("score", 0))
    score_lbl  = score_data.get("score_label", "")
    mode_lbl   = "Desenvolvimento" if audit_mode == "development" else "Operacional"
    date_str   = datetime.now().strftime("%d/%m/%Y")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT + 1.5*cm,   # space for header bar
        bottomMargin=MB + 1.2*cm, # space for footer
        title=f"CO2mply | Compliance Matrix — {project_name}",
        author="CO2mply",
    )

    cb = _make_page_cb(project_name, date_str)
    story = []

    # ── Logo ────────────────────────────────────────────────────────────────────
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=5.5*cm, height=2.0*cm)
        logo.hAlign = "LEFT"
        story.append(logo)
        story.append(Spacer(1, 0.3*cm))
    else:
        story.append(_p('<font name="Helvetica-Bold" size="18" color="#1A3160">CO2mply</font>',
                        _style(fontSize=18)))
        story.append(Spacer(1, 0.3*cm))

    # ── Title block ─────────────────────────────────────────────────────────────
    story.append(_p("Compliance Audit Report",
                    _style(fontName="Helvetica-Bold", fontSize=22, leading=28,
                           textColor=_c(NAVY), spaceAfter=4)))
    story.append(_p(f"Padrão: {methodology}  ·  Modo: {mode_lbl}",
                    _style(fontSize=10, leading=14, textColor=_c(TEXT2), spaceAfter=2)))
    story.append(_p(f"Projeto: {project_name}  ·  Data: {date_str}",
                    _style(fontSize=10, leading=14, textColor=_c(TEXT2), spaceAfter=10)))
    story.append(HRFlowable(width="100%", thickness=1, color=_c(BORDER)))
    story.append(Spacer(1, 0.5*cm))

    # ── KPI block ────────────────────────────────────────────────────────────────
    counts = {}
    for r in results:
        s = r.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    n_conf   = counts.get("compliant", 0)
    n_part   = counts.get("partial", 0) + counts.get("future_evidence_required", 0)
    n_nonc   = counts.get("non_compliant", 0)
    n_na     = counts.get("not_applicable", 0)

    score_color = GREEN if score >= 85 else AMBER if score >= 60 else RED

    kpi_col_w = (PAGE_W - ML - MR) / 5

    # Two-row KPI table: values row + labels row
    kpi_table = Table(
        [
            # Row 1: values
            [
                _p(f'<font name="Helvetica-Bold" size="22" color="{score_color}">{score:.0f}%</font>',
                   _style(alignment=TA_CENTER, fontSize=22, leading=26)),
                _p(f'<font name="Helvetica-Bold" size="18" color="{GREEN}">{n_conf}</font>',
                   _style(alignment=TA_CENTER, fontSize=18, leading=22)),
                _p(f'<font name="Helvetica-Bold" size="18" color="{AMBER}">{n_part}</font>',
                   _style(alignment=TA_CENTER, fontSize=18, leading=22)),
                _p(f'<font name="Helvetica-Bold" size="18" color="{RED if n_nonc else GRAY_MID}">{n_nonc}</font>',
                   _style(alignment=TA_CENTER, fontSize=18, leading=22)),
                _p(f'<font name="Helvetica-Bold" size="18" color="{GRAY_MID}">{n_na}</font>',
                   _style(alignment=TA_CENTER, fontSize=18, leading=22)),
            ],
            # Row 2: labels
            [
                _p(f'<font size="8" color="{TEXT2}">{score_lbl}</font>',
                   _style(alignment=TA_CENTER, fontSize=8, leading=10)),
                _p(f'<font size="8" color="{TEXT2}">Conformes</font>',
                   _style(alignment=TA_CENTER, fontSize=8, leading=10)),
                _p(f'<font size="8" color="{TEXT2}">Parciais</font>',
                   _style(alignment=TA_CENTER, fontSize=8, leading=10)),
                _p(f'<font size="8" color="{TEXT2}">Não conf.</font>',
                   _style(alignment=TA_CENTER, fontSize=8, leading=10)),
                _p(f'<font size="8" color="{TEXT2}">N/A (op.)</font>',
                   _style(alignment=TA_CENTER, fontSize=8, leading=10)),
            ],
        ],
        colWidths=[kpi_col_w] * 5,
        rowHeights=[1.4*cm, 0.7*cm],
    )
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _c(NAVY_LIGHT)),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("LINEAFTER",     (0, 0), (3, 0), 0.5, _c(BORDER)),
        ("BOX",           (0, 0), (-1, -1), 0.5, _c(BORDER)),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.7*cm))

    # ── Matrix ───────────────────────────────────────────────────────────────────

    TABLE_W = PAGE_W - ML - MR
    COL_W   = [2.8*cm, TABLE_W - 2.8*cm - 2.6*cm - 1.6*cm, 2.6*cm, 1.6*cm]

    s_id    = _style(fontName="Helvetica-Bold", fontSize=8, textColor=_c(NAVY), leading=11)
    s_req   = _style(fontName="Helvetica-Bold", fontSize=8.5, leading=12)
    s_note  = _style(fontName="Helvetica-Oblique", fontSize=7.5, textColor=_c(GRAY_DARK),
                     leading=10, leftIndent=0, spaceAfter=1)
    s_hdr   = _style(fontName="Helvetica-Bold", fontSize=7, textColor=_c(TEXT2),
                     alignment=TA_LEFT, leading=9)
    s_hdr_c = _style(fontName="Helvetica-Bold", fontSize=7, textColor=_c(TEXT2),
                     alignment=TA_CENTER, leading=9)
    s_mod   = _style(fontName="Helvetica-Bold", fontSize=9, textColor=_c("#FFFFFF"),
                     leading=12)

    def _col_header_row():
        return [
            _p("ID", s_hdr),
            _p("REQUISITO", s_hdr),
            _p("STATUS", s_hdr_c),
            _p("SCORE", s_hdr_c),
        ]

    groups = _group_by_module(results)

    for module_name, reqs in groups.items():
        # Module header
        mod_header = Table(
            [[_p(module_name.upper(), s_mod)]],
            colWidths=[TABLE_W],
        )
        mod_header.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _c(NAVY)),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))

        # Column header row + all requirement rows
        table_data = [_col_header_row()]
        row_styles = [
            # Column header row styling
            ("BACKGROUND",    (0, 0), (-1, 0), _c("#F1F5F9")),
            ("LINEBELOW",     (0, 0), (-1, 0), 0.5, _c(BORDER)),
            ("TOPPADDING",    (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ]

        for i, req in enumerate(reqs, start=1):
            status  = req.get("status", "")
            lbl     = _lbl(status)
            fg      = _fg(status)
            bg      = _bg(status)
            sc_str  = _score_str(req)
            sc_col  = _score_color(req)
            req_id  = req.get("requirement_id", "")
            title   = req.get("title") or req.get("requirement_name", "")

            # Gap
            gap = (req.get("gap") or "").strip()
            if gap in GENERIC: gap = ""

            # Notes
            notes = _clean_notes(req.get("notes"))

            # Build requirement cell
            req_cell_content = [_p(title, s_req)]
            if status == "not_applicable":
                req_cell_content.append(_p(
                    "Evidência aplicável em Modo Operacional — não penaliza o score.", s_note))
            else:
                if gap:
                    req_cell_content.append(_p(f"→ {gap}", s_note))
                for n in notes[:2]:
                    req_cell_content.append(_p(f"• {n}", s_note))

            # Status badge paragraph
            s_badge = _style(
                fontName="Helvetica-Bold", fontSize=8,
                textColor=_c(fg), alignment=TA_CENTER, leading=10,
            )
            s_score = _style(
                fontName="Helvetica-Bold", fontSize=9.5,
                textColor=_c(sc_col), alignment=TA_CENTER, leading=11,
            )

            table_data.append([
                _p(req_id, s_id),
                req_cell_content,
                _p(lbl, s_badge),
                _p(sc_str, s_score),
            ])

            row_styles += [
                ("BACKGROUND",    (0, i), (-1, i), _c(bg)),
                ("TOPPADDING",    (0, i), (-1, i), 6),
                ("BOTTOMPADDING", (0, i), (-1, i), 6),
                ("LINEBELOW",     (0, i), (-1, i), 0.3, _c(BORDER)),
                ("VALIGN",        (0, i), (-1, i), "TOP"),
                ("ALIGN",         (2, i), (3, i),  "CENTER"),
                ("VALIGN",        (2, i), (3, i),  "MIDDLE"),
                # Left accent bar by status color
                ("LINEBEFORE",    (0, i), (0, i),  3, _c(fg)),
            ]

        row_styles += [
            # All rows: padding & font
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  7),
        ]

        module_table = Table(table_data, colWidths=COL_W, repeatRows=1)
        module_table.setStyle(TableStyle(row_styles))

        # KeepTogether só para o header + linha de colunas — a tabela pode quebrar
        story.append(KeepTogether([mod_header, Spacer(1, 1)]))
        story.append(module_table)
        story.append(Spacer(1, 0.5*cm))

    # ── Footer note ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.4, color=_c(BORDER)))
    story.append(Spacer(1, 0.2*cm))
    story.append(_p(
        "Este relatório foi gerado automaticamente pelo motor determinístico CO2mply. "
        "Os resultados refletem a análise dos documentos do projeto contra os critérios do "
        "protocolo selecionado. Documento confidencial — para uso exclusivo do proponente do projeto.",
        _style(fontName="Helvetica-Oblique", fontSize=7, textColor=_c(GRAY_MID), leading=10),
    ))

    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    return buf.getvalue()
