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

_ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Usar logo transparente (fundo removido, cropada); fallback para original
LOGO_PATH = os.path.join(_ASSETS, "assets", "logo_transparent.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(_ASSETS, "assets", "auditoria_logo.png")
# Ratio do logo transparente cropado: 743×320 = 2.32
LOGO_RATIO = 743 / 320

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

        # Header bar — 1.6cm, fundo cinza claro
        HDR_H = 1.6 * cm
        canvas.setFillColor(_c("#F1F5F9"))
        canvas.rect(0, h - HDR_H, w, HDR_H, fill=1, stroke=0)
        canvas.setStrokeColor(_c(NAVY))
        canvas.setLineWidth(1.2)
        canvas.line(0, h - HDR_H, w, h - HDR_H)

        # Logo transparente, centralizada verticalmente na barra
        # Ratio 743×320 = 2.32 | altura = header - 2×padding
        PAD_V = 0.15 * cm
        LOGO_H = HDR_H - 2 * PAD_V          # altura ajustada à barra
        LOGO_W = LOGO_H * LOGO_RATIO         # largura proporcional
        LOGO_Y = h - HDR_H + PAD_V
        if os.path.exists(LOGO_PATH):
            canvas.drawImage(
                LOGO_PATH,
                ML, LOGO_Y,
                width=LOGO_W, height=LOGO_H,
                preserveAspectRatio=True, mask="auto",
            )

        # Texto direito
        canvas.setFillColor(_c(NAVY))
        canvas.setFont("Helvetica", 8.5)
        canvas.drawRightString(w - MR, h - HDR_H/2 - 0.15*cm, "Carbon Compliance Intelligence")

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
        topMargin=MT + 1.8*cm,   # space for header bar (1.6cm)
        bottomMargin=MB + 1.2*cm, # space for footer
        title=f"CO2mply | Compliance Matrix — {project_name}",
        author="CO2mply",
    )

    cb = _make_page_cb(project_name, date_str)
    story = []

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


# ── Project Readiness Certificate PDF ─────────────────────────────────────────

def generate_readiness_certificate_pdf(
    rating: Dict[str, Any],
    project_name: str = "Projeto",
    methodology: str = "Isometric Biochar",
) -> bytes:
    """Single-page certificate of Project Readiness Score."""
    grade       = rating.get("grade", "C")
    label       = rating.get("label", "")
    description = rating.get("description", "")
    overall     = float(rating.get("overall_score", 0))
    audit_mode  = rating.get("audit_mode", "development")
    phase       = rating.get("phase", "PDD Audit")
    dims        = rating.get("dimensions", {})
    date_str    = datetime.now().strftime("%d/%m/%Y")

    GRADE_COLORS = {
        "A+": (GREEN, GREEN_BG), "A":  (GREEN, GREEN_BG),
        "B+": (AMBER, AMBER_BG), "B":  (AMBER, AMBER_BG),
        "C":  (RED,   RED_BG),
    }
    grade_fg, grade_bg = GRADE_COLORS.get(grade, (GRAY_MID, GRAY_BG))

    DIM_LABELS = {
        "carbon": "Carbon Accounting", "additionality": "Additionality",
        "permanence": "Permanência",   "safeguards": "Salvaguardas",
        "integrity": "Integridade PDD",
    }
    DIM_ORDER = ["carbon", "additionality", "permanence", "safeguards", "integrity"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2.0*cm, rightMargin=2.0*cm,
        topMargin=1.6*cm, bottomMargin=1.6*cm,
        title=f"CO2mply | Project Readiness Certificate — {project_name}",
        author="CO2mply",
    )
    TABLE_W = PAGE_W - 4.0*cm
    story   = []

    # ── Logo + heading ─────────────────────────────────────────────────────────
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=1.6*cm * LOGO_RATIO, height=1.6*cm)
        logo.hAlign = "LEFT"
        story.append(logo)
    story.append(Spacer(1, 0.25*cm))
    story.append(_p("CERTIFICADO DE PRONTIDÃO DO PROJETO",
        _style(fontName="Helvetica-Bold", fontSize=10, leading=13,
               textColor=_c(TEXT2), letterSpacing=1.5)))
    story.append(_p("Project Readiness Certificate",
        _style(fontName="Helvetica-Bold", fontSize=26, leading=32,
               textColor=_c(NAVY), spaceAfter=5)))
    story.append(HRFlowable(width="100%", thickness=2.5, color=_c(NAVY)))
    story.append(Spacer(1, 0.4*cm))

    # ── Project info bar ───────────────────────────────────────────────────────
    info = Table([[
        _p(f'<b>Projeto:</b> {project_name}', _style(fontSize=11, leading=15)),
        _p(f'<b>Padrão:</b> {methodology}',   _style(fontSize=11, leading=15, alignment=TA_CENTER)),
        _p(f'<b>Data:</b> {date_str}',        _style(fontSize=11, leading=15, alignment=TA_RIGHT)),
    ]], colWidths=[TABLE_W*0.45, TABLE_W*0.35, TABLE_W*0.20])
    info.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), _c(NAVY_LIGHT)),
        ("TOPPADDING",    (0,0),(-1,-1), 9), ("BOTTOMPADDING", (0,0),(-1,-1), 9),
        ("LEFTPADDING",   (0,0),(-1,-1), 12), ("RIGHTPADDING",  (0,0),(-1,-1), 12),
        ("BOX", (0,0),(-1,-1), 0.5, _c(BORDER)),
    ]))
    story.append(info)
    story.append(Spacer(1, 0.6*cm))

    # ── Grade block ────────────────────────────────────────────────────────────
    GRADE_W = 4.2*cm
    grade_cell = Table([[
        _p(grade, _style(fontName="Helvetica-Bold", fontSize=96, leading=106,
                         textColor=_c(grade_fg), alignment=TA_CENTER)),
    ]], colWidths=[GRADE_W], rowHeights=[4.0*cm])
    grade_cell.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), _c(grade_bg)),
        ("ALIGN",  (0,0),(-1,-1), "CENTER"), ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ("BOX",    (0,0),(-1,-1), 3, _c(grade_fg)),
    ]))

    verdict = [
        _p(label, _style(fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=_c(grade_fg))),
        Spacer(1, 0.15*cm),
        _p(f'Score: <b>{overall:.1f}%</b>  ·  {phase}  ·  '
           f'Modo {"Desenvolvimento" if audit_mode == "development" else "Operacional"}',
           _style(fontSize=10, leading=14, textColor=_c(TEXT2))),
        Spacer(1, 0.25*cm),
        _p(description, _style(fontSize=11, leading=16, textColor=_c(TEXT))),
    ]
    main_row = Table([[grade_cell, verdict]],
                     colWidths=[GRADE_W + 0.8*cm, TABLE_W - GRADE_W - 0.8*cm])
    main_row.setStyle(TableStyle([
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (1,0),(1,0), 22),
        ("TOPPADDING",    (0,0),(-1,-1), 0), ("BOTTOMPADDING", (0,0),(-1,-1), 0),
    ]))
    story.append(main_row)
    story.append(Spacer(1, 0.6*cm))

    # ── Dimensional scores — sem N/A nos labels ────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.7, color=_c(BORDER)))
    story.append(Spacer(1, 0.3*cm))
    story.append(_p("Avaliação por Dimensão",
        _style(fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=_c(NAVY), spaceAfter=7)))

    col_w = TABLE_W / len(DIM_ORDER)
    lbl_row, sc_row, bar_row = [], [], []
    total_na = 0
    for dk in DIM_ORDER:
        dim = dims.get(dk, {})
        s   = float(dim.get("score", 0))
        na  = dim.get("na_count", 0)
        total_na += na
        sc  = GREEN if s >= 80 else AMBER if s >= 60 else RED

        # Label sem N/A — limpo
        lbl_row.append(_p(DIM_LABELS.get(dk, dk),
            _style(fontName="Helvetica-Bold", fontSize=8, leading=11,
                   alignment=TA_CENTER, textColor=_c(TEXT2))))
        sc_row.append(_p(f"{s:.0f}%",
            _style(fontName="Helvetica-Bold", fontSize=20, leading=26,
                   alignment=TA_CENTER, textColor=_c(sc))))

        inner_w = col_w - 0.8*cm
        fill_w  = max(0.05, inner_w * s / 100)
        rest_w  = max(0.05, inner_w - fill_w)
        bar = Table([["", ""]], colWidths=[fill_w, rest_w])
        bar.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(0,0), _c(sc)),
            ("BACKGROUND",    (1,0),(1,0), _c(BORDER)),
            ("TOPPADDING",    (0,0),(-1,-1), 5), ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 0), ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ]))
        bar_row.append(bar)

    dim_tbl = Table([lbl_row, sc_row, bar_row], colWidths=[col_w]*len(DIM_ORDER))
    dim_tbl.setStyle(TableStyle([
        ("ALIGN",  (0,0),(-1,-1), "CENTER"), ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,0), 8), ("BOTTOMPADDING", (0,0),(-1,0), 5),
        ("TOPPADDING",    (0,1),(-1,1), 4), ("BOTTOMPADDING", (0,1),(-1,1), 5),
        ("TOPPADDING",    (0,2),(-1,2), 3), ("BOTTOMPADDING", (0,2),(-1,2), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 4), ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("LINEAFTER",     (0,0),(3,-1), 0.4, _c(BORDER)),
        ("BOX",           (0,0),(-1,-1), 0.5, _c(BORDER)),
        ("BACKGROUND",    (0,0),(-1, 0), _c(NAVY_LIGHT)),
    ]))
    story.append(dim_tbl)
    story.append(Spacer(1, 0.3*cm))

    # Nota explicativa sobre N/A — clara e discreta
    if total_na > 0 and audit_mode == "development":
        story.append(_p(
            f"* {total_na} critério(s) marcados como 'Não Aplicável' nesta avaliação — "
            f"aplicáveis apenas quando o projeto estiver em operação (análises laboratoriais, "
            f"amostras reais, dados de monitoramento). Não penalizam o score em Modo Desenvolvimento.",
            _style(fontSize=8, leading=11, textColor=_c(GRAY_DARK),
                   fontName="Helvetica-Oblique")))
        story.append(Spacer(1, 0.35*cm))

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=_c(BORDER)))
    story.append(Spacer(1, 0.2*cm))
    story.append(_p(
        f"Este certificado atesta que o projeto <b>{project_name}</b> foi avaliado pelo motor "
        f"determinístico CO2mply contra os critérios do protocolo <b>{methodology}</b> em <b>{date_str}</b>. "
        f"O Project Readiness Score avalia a completude e consistência documental do PDD — "
        f"é uma auditoria de prontidão, não uma rating de crédito de carbono. "
        f"CO2mply · Carbon Compliance Intelligence · v1.0",
        _style(fontName="Helvetica-Oblique", fontSize=7.5, leading=11, textColor=_c(GRAY_MID))))

    doc.build(story)
    return buf.getvalue()


# ── Audit Summary PDF ──────────────────────────────────────────────────────────

def generate_audit_summary_pdf(
    results: List[dict],
    score_data: dict,
    audit_mode: str = "development",
    project_name: str = "Projeto",
    methodology: str = "Isometric Biochar",
) -> bytes:
    """Executive-style audit summary: 2-3 pages, only what matters."""

    score      = float(score_data.get("score", 0))
    score_lbl  = score_data.get("score_label", "")
    mode_lbl   = "Desenvolvimento" if audit_mode == "development" else "Operacional"
    date_str   = datetime.now().strftime("%d/%m/%Y")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT + 1.8*cm,
        bottomMargin=MB + 1.2*cm,
        title=f"CO2mply | Resumo de Auditoria — {project_name}",
        author="CO2mply",
    )

    cb = _make_page_cb(project_name, date_str)
    story = []

    TABLE_W = PAGE_W - ML - MR
    score_color = GREEN if score >= 85 else AMBER if score >= 60 else RED

    # ── Header block ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.2*cm))
    story.append(_p("Resumo Executivo de Auditoria",
                    _style(fontName="Helvetica-Bold", fontSize=20, leading=26,
                           textColor=_c(NAVY), spaceAfter=4)))
    story.append(_p(f"Padrão: {methodology}  ·  Modo: {mode_lbl}",
                    _style(fontSize=10, leading=14, textColor=_c(TEXT2), spaceAfter=2)))
    story.append(_p(f"Projeto: {project_name}  ·  Data: {date_str}",
                    _style(fontSize=10, leading=14, textColor=_c(TEXT2), spaceAfter=8)))
    story.append(HRFlowable(width="100%", thickness=1, color=_c(BORDER)))
    story.append(Spacer(1, 0.4*cm))

    # ── Score banner ───────────────────────────────────────────────────────────
    counts = {}
    for r in results:
        s = r.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    n_conf  = counts.get("compliant", 0)
    n_part  = counts.get("partial", 0) + counts.get("future_evidence_required", 0)
    n_nonc  = counts.get("non_compliant", 0)
    n_na    = counts.get("not_applicable", 0)
    n_total = n_conf + n_part + n_nonc  # excluindo N/A

    # Score + verdict box
    verdict = (
        "O projeto demonstra alta aderência ao protocolo. "
        "Os gaps identificados são documentais e de fácil resolução antes da submissão."
        if score >= 80 else
        "O projeto apresenta boa estrutura mas requer complementação em seções importantes "
        "antes da submissão para validação."
        if score >= 65 else
        "O projeto necessita de atenção significativa antes da submissão. "
        "Veja os gaps prioritários abaixo."
    )

    score_banner = Table(
        [[
            # Score — coluna mais larga para "87%" caber em uma linha
            _p(f'<font name="Helvetica-Bold" size="30" color="{score_color}">{score:.0f}%</font>',
               _style(alignment=TA_CENTER, fontSize=30, leading=36)),
            # Verdict text
            [
                _p(f'<font name="Helvetica-Bold" size="12" color="{score_color}">{score_lbl}</font>',
                   _style(fontSize=12, fontName="Helvetica-Bold", leading=16,
                          textColor=_c(score_color))),
                _p(verdict, _style(fontSize=9, leading=13, textColor=_c(TEXT2))),
                Spacer(1, 0.2*cm),
                _p(f'<font size="8" color="{TEXT2}">Requisitos avaliados: {n_total}  '
                   f'|  Não aplicáveis (modo operacional): {n_na}</font>',
                   _style(fontSize=8, leading=11, textColor=_c(TEXT2))),
            ],
        ]],
        colWidths=[4.0*cm, TABLE_W - 4.0*cm],
    )
    score_banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _c(NAVY_LIGHT)),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (0, 0),   "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEAFTER",     (0, 0), (0, 0),   0.5, _c(BORDER)),
        ("BOX",           (0, 0), (-1, -1), 0.5, _c(BORDER)),
    ]))
    story.append(score_banner)
    story.append(Spacer(1, 0.5*cm))

    # ── Status summary row ─────────────────────────────────────────────────────
    kpi_col = TABLE_W / 3

    def _sum_kpi(val, lbl, color, sub=""):
        return [
            _p(f'<font name="Helvetica-Bold" size="22" color="{color}">{val}</font>',
               _style(alignment=TA_CENTER, fontSize=22, leading=26)),
            _p(f'<font size="8.5" color="{TEXT2}"><b>{lbl}</b></font>',
               _style(alignment=TA_CENTER, fontSize=8.5, leading=11)),
        ] + ([_p(f'<font size="7.5" color="{GRAY_MID}">{sub}</font>',
                 _style(alignment=TA_CENTER, fontSize=7.5, leading=9))] if sub else [])

    kpi_row = Table(
        [[
            _sum_kpi(str(n_conf),  "✓ Conformes",    GREEN),
            _sum_kpi(str(n_part),  "⚠ Parciais / Ev. futura", AMBER),
            _sum_kpi(str(n_nonc),  "✗ Não conformes", RED if n_nonc else GRAY_MID),
        ]],
        colWidths=[kpi_col] * 3,
    )
    kpi_row.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEAFTER",     (0, 0), (1, 0),   0.5, _c(BORDER)),
        ("BOX",           (0, 0), (-1, -1), 0.5, _c(BORDER)),
    ]))
    story.append(kpi_row)
    story.append(Spacer(1, 0.6*cm))

    # ── Gaps prioritários ──────────────────────────────────────────────────────
    gaps = [r for r in results
            if r.get("status") in ("partial", "non_compliant", "future_evidence_required")]
    gaps.sort(key=lambda r: (r.get("requirement_score") or 0))  # pior score primeiro

    if gaps:
        # Section header
        sec_hdr = Table(
            [[_p("GAPS PRIORITÁRIOS — AÇÕES RECOMENDADAS",
                 _style(fontName="Helvetica-Bold", fontSize=9, textColor=_c("#FFFFFF"), leading=12))]],
            colWidths=[TABLE_W],
        )
        sec_hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _c(NAVY)),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        story.append(sec_hdr)
        story.append(Spacer(1, 2))

        s_gap_id  = _style(fontName="Helvetica-Bold", fontSize=8, textColor=_c(NAVY), leading=11)
        s_gap_ttl = _style(fontName="Helvetica-Bold", fontSize=9, leading=12)
        s_gap_txt = _style(fontSize=8.5, leading=11, textColor=_c(TEXT2))
        s_gap_act = _style(fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=_c(GREEN))

        GAP_W = [2.2*cm, TABLE_W - 2.2*cm - 1.4*cm, 1.4*cm]

        # Column headers
        col_hdr = Table([[
            _p("ID", _style(fontName="Helvetica-Bold", fontSize=7, textColor=_c(TEXT2))),
            _p("REQUISITO / AÇÃO RECOMENDADA",
               _style(fontName="Helvetica-Bold", fontSize=7, textColor=_c(TEXT2))),
            _p("SCORE", _style(fontName="Helvetica-Bold", fontSize=7,
                               textColor=_c(TEXT2), alignment=TA_CENTER)),
        ]], colWidths=GAP_W)
        col_hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _c("#F1F5F9")),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.5, _c(BORDER)),
        ]))
        story.append(col_hdr)

        for req in gaps:
            status = req.get("status", "")
            lbl, fg, bg = STATUS.get(status, ("?", GRAY_MID, GRAY_BG))
            sc   = _score_str(req)
            sc_c = _score_color(req)
            rid  = req.get("requirement_id", "")
            ttl  = req.get("title") or req.get("requirement_name", "")

            gap = (req.get("gap") or "").strip()
            if gap in GENERIC: gap = ""

            notes = _clean_notes(req.get("notes"))

            rec = (req.get("recommendation") or "").strip()
            if rec in GENERIC: rec = ""

            # Build content cell
            content = [_p(ttl, s_gap_ttl)]
            if gap:
                content.append(_p(f"Gap: {gap}", s_gap_txt))
            elif notes:
                content.append(_p(f"Gap: {notes[0]}", s_gap_txt))
            if rec:
                content.append(_p(f"→ {rec}", s_gap_act))

            row = Table([[
                _p(f'{rid}\n<font size="7" color="{fg}"><b>{lbl}</b></font>', s_gap_id),
                content,
                _p(sc, _style(fontName="Helvetica-Bold", fontSize=11,
                               textColor=_c(sc_c), alignment=TA_CENTER)),
            ]], colWidths=GAP_W)
            row.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), _c(bg)),
                ("TOPPADDING",    (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("ALIGN",         (2, 0), (2, 0),   "CENTER"),
                ("VALIGN",        (2, 0), (2, 0),   "MIDDLE"),
                ("LINEBELOW",     (0, 0), (-1, -1), 0.3, _c(BORDER)),
                ("LINEBEFORE",    (0, 0), (0, 0),   3, _c(fg)),
            ]))
            story.append(row)

    story.append(Spacer(1, 0.6*cm))

    # ── N/A note ──────────────────────────────────────────────────────────────
    if n_na > 0:
        story.append(_p(
            f"ℹ {n_na} requisito(s) marcados como N/A — aplicáveis apenas em projetos operacionais "
            f"(análises laboratoriais, amostragem real, temperatura do solo). "
            f"Não penalizam o score em Modo Desenvolvimento.",
            _style(fontSize=8, leading=11, textColor=_c(TEXT2),
                   fontName="Helvetica-Oblique"),
        ))
        story.append(Spacer(1, 0.4*cm))

    # ── Footer note ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.4, color=_c(BORDER)))
    story.append(Spacer(1, 0.2*cm))
    story.append(_p(
        "Este resumo foi gerado automaticamente pelo motor determinístico CO2mply. "
        "Os resultados refletem a análise dos documentos do projeto contra os critérios do "
        "protocolo selecionado. Documento confidencial — para uso exclusivo do proponente do projeto.",
        _style(fontName="Helvetica-Oblique", fontSize=7, textColor=_c(GRAY_MID), leading=10),
    ))

    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    return buf.getvalue()
