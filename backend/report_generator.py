"""
CO2mply — Professional PDF Report Generator
Uses ReportLab to produce branded compliance audit reports.
"""
import io
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable, PageBreak,
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.utils import ImageReader

# ── Brand colours ─────────────────────────────────────────────────────────────

C_NAVY       = colors.HexColor("#1A3160")   # primary navy (sidebar)
C_NAVY_LIGHT = colors.HexColor("#E8EDF5")   # very light navy tint
C_GREEN      = colors.HexColor("#16A34A")   # compliant
C_GREEN_BG   = colors.HexColor("#F0FDF4")
C_AMBER      = colors.HexColor("#D97706")   # partial
C_AMBER_BG   = colors.HexColor("#FFFBEB")
C_PURPLE     = colors.HexColor("#7C3AED")   # future_evidence
C_PURPLE_BG  = colors.HexColor("#F5F3FF")
C_RED        = colors.HexColor("#DC2626")   # non_compliant
C_RED_BG     = colors.HexColor("#FEF2F2")
C_GRAY       = colors.HexColor("#6B7280")   # N/A
C_GRAY_BG    = colors.HexColor("#F9FAFB")
C_BORDER     = colors.HexColor("#E5E7EB")
C_TEXT       = colors.HexColor("#0F172A")
C_TEXT2      = colors.HexColor("#475569")
C_WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN_L = 2.0 * cm
MARGIN_R = 2.0 * cm
MARGIN_T = 2.5 * cm
MARGIN_B = 2.0 * cm

LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "auditoria_logo.png"
)

# ── Status config ──────────────────────────────────────────────────────────────

STATUS_CONFIG = {
    "compliant":                ("Conforme",         C_GREEN,  C_GREEN_BG),
    "partial":                  ("Parcial",           C_AMBER,  C_AMBER_BG),
    "future_evidence_required": ("Ev. Futura",        C_PURPLE, C_PURPLE_BG),
    "non_compliant":            ("Não conforme",      C_RED,    C_RED_BG),
    "not_applicable":           ("N/A",               C_GRAY,   C_GRAY_BG),
    "error":                    ("Erro",              C_GRAY,   C_GRAY_BG),
}

GENERIC_MESSAGES = {
    "Maintain current evidence and proceed to validation readiness.",
    "Partial evidence available; some required elements are incomplete.",
    "Core requirement not met or insufficiently evidenced.",
    "Provide missing documentation and strengthen evidence for identified gaps.",
    "Strengthen consistency and completeness of existing evidence.",
    "Establish missing core elements required for compliance.",
    "Correct failed conditions and provide full supporting evidence before validation.",
    "Providencie esta evidência quando o projeto estiver operacional.",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def _status_label(status: str) -> str:
    return STATUS_CONFIG.get(status, ("?", C_GRAY, C_GRAY_BG))[0]

def _status_color(status: str) -> colors.Color:
    return STATUS_CONFIG.get(status, ("?", C_GRAY, C_GRAY_BG))[1]

def _status_bg(status: str) -> colors.Color:
    return STATUS_CONFIG.get(status, ("?", C_GRAY, C_GRAY_BG))[2]

def _clean_notes(notes) -> List[str]:
    if isinstance(notes, list):
        return [n for n in notes
                if n and not n.startswith("[Protocolo]")
                and "desenvolvimento:" not in n.lower()
                and "operacional:" not in n.lower()
                and n not in GENERIC_MESSAGES]
    return []

def _score_str(r: dict) -> str:
    s = r.get("requirement_score") or r.get("score")
    if r.get("status") == "not_applicable" or s is None:
        return "N/A"
    try:
        return str(int(round(float(s))))
    except Exception:
        return "N/A"

def _score_color(r: dict) -> colors.Color:
    s = r.get("requirement_score") or r.get("score")
    if s is None:
        return C_GRAY
    try:
        v = float(s)
        if v >= 85:  return C_GREEN
        if v >= 60:  return C_AMBER
        return C_RED
    except Exception:
        return C_GRAY

def _group_by_module(results: List[dict]) -> Dict[str, List[dict]]:
    groups: Dict[str, List[dict]] = {}
    for r in results:
        mod = (r.get("module") or "other").replace("_", " ").title()
        groups.setdefault(mod, []).append(r)
    return groups

# ── Page template (header/footer via canvas callbacks) ─────────────────────────

class _HeaderFooter:
    def __init__(self, project_name: str, date_str: str):
        self.project_name = project_name
        self.date_str = date_str

    def on_page(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        # ── Top header bar ──────────────────────────────────────────────────
        canvas.setFillColor(C_NAVY)
        canvas.rect(0, h - 1.4 * cm, w, 1.4 * cm, fill=1, stroke=0)

        canvas.setFillColor(C_WHITE)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN_L, h - 0.9 * cm, "CO2mply")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - MARGIN_R, h - 0.9 * cm, "Carbon Compliance Intelligence")

        # ── Bottom footer ────────────────────────────────────────────────────
        canvas.setFillColor(C_BORDER)
        canvas.rect(MARGIN_L, 1.3 * cm, w - MARGIN_L - MARGIN_R, 0.03 * cm, fill=1, stroke=0)

        canvas.setFillColor(C_TEXT2)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(MARGIN_L, 0.7 * cm,
                          f"CO2mply | Auditoria de Conformidade — {self.project_name}")
        canvas.drawRightString(w - MARGIN_R, 0.7 * cm,
                               f"Página {doc.page}  |  {self.date_str}")

        # ── Confidential watermark ────────────────────────────────────────
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(C_GRAY)
        canvas.drawCentredString(w / 2, 0.7 * cm, "CONFIDENCIAL")

        canvas.restoreState()


# ── Score circle (custom Flowable) ─────────────────────────────────────────────

class ScoreCircle(Flowable):
    def __init__(self, score: float, label: str, size: float = 2.8 * cm):
        Flowable.__init__(self)
        self.score = score
        self.label = label
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        r = self.size / 2
        cx, cy = r, r

        # Background circle
        self.canv.setFillColor(C_NAVY_LIGHT)
        self.canv.circle(cx, cy, r, fill=1, stroke=0)

        # Color ring (arc drawn as a series of lines — simplified as colored circle)
        score = self.score
        if score >= 85:   ring_color = C_GREEN
        elif score >= 60: ring_color = C_AMBER
        else:             ring_color = C_RED
        self.canv.setStrokeColor(ring_color)
        self.canv.setLineWidth(4)
        self.canv.circle(cx, cy, r - 3, fill=0, stroke=1)

        # Score text
        self.canv.setFillColor(C_NAVY)
        self.canv.setFont("Helvetica-Bold", 16)
        score_str = f"{score:.0f}%"
        self.canv.drawCentredString(cx, cy + 2, score_str)

        # Label
        self.canv.setFont("Helvetica", 6)
        self.canv.setFillColor(C_TEXT2)
        self.canv.drawCentredString(cx, cy - 9, self.label)


# ── Main generator ─────────────────────────────────────────────────────────────

def generate_compliance_matrix_pdf(
    results: List[dict],
    score_data: dict,
    audit_mode: str = "development",
    project_name: str = "Projeto",
    methodology: str = "Isometric Biochar",
) -> bytes:
    """Generate a professional compliance matrix PDF."""
    buffer = io.BytesIO()

    score = float(score_data.get("score", 0))
    score_label = score_data.get("score_label", "")
    mode_label = "Desenvolvimento" if audit_mode == "development" else "Operacional"
    date_str = datetime.now().strftime("%d/%m/%Y")

    hf = _HeaderFooter(project_name, date_str)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T + 0.3 * cm,
        bottomMargin=MARGIN_B + 0.8 * cm,
        title=f"CO2mply | Compliance Matrix — {project_name}",
        author="CO2mply",
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Cover / Header block ──────────────────────────────────────────────────

    # Logo
    if os.path.exists(LOGO_PATH):
        from reportlab.platypus import Image
        logo = Image(LOGO_PATH, width=6 * cm, height=2.2 * cm)
        logo.hAlign = "LEFT"
        story.append(logo)
    else:
        story.append(Paragraph(
            '<font size="20" color="#1A3160"><b>CO2mply</b></font>',
            ParagraphStyle("logo", fontName="Helvetica-Bold", fontSize=20)
        ))

    story.append(Spacer(1, 0.5 * cm))

    # Title
    title_style = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=C_NAVY,
        spaceAfter=4,
    )
    story.append(Paragraph("Compliance Audit Report", title_style))

    sub_style = ParagraphStyle(
        "cover_sub",
        fontName="Helvetica",
        fontSize=11,
        textColor=C_TEXT2,
        spaceAfter=2,
    )
    story.append(Paragraph(f"Padrão: {methodology}  |  Modo: {mode_label}", sub_style))
    story.append(Paragraph(f"Projeto: {project_name}  |  Data: {date_str}", sub_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    story.append(Spacer(1, 0.5 * cm))

    # ── Score summary row ──────────────────────────────────────────────────────

    counts = {}
    for r in results:
        s = r.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    n_compliant = counts.get("compliant", 0)
    n_partial   = counts.get("partial", 0) + counts.get("future_evidence_required", 0)
    n_noncomp   = counts.get("non_compliant", 0)
    n_na        = counts.get("not_applicable", 0)
    n_total     = sum(c for s, c in counts.items() if s != "not_applicable")

    def _kpi_cell(value: str, label: str, color: colors.Color) -> List:
        return [
            Paragraph(f'<font size="22" color="{color.hexval()}"><b>{value}</b></font>',
                      ParagraphStyle("kpi", alignment=TA_CENTER)),
            Paragraph(f'<font size="8" color="#6B7280">{label}</font>',
                      ParagraphStyle("kpi_lbl", alignment=TA_CENTER)),
        ]

    if score >= 85:   score_c = C_GREEN
    elif score >= 60: score_c = C_AMBER
    else:             score_c = C_RED

    kpi_table = Table(
        [[
            ScoreCircle(score, score_label or "Score", size=3.2 * cm),
            Table([_kpi_cell(str(n_compliant), "Conformes", C_GREEN)],   colWidths=[3.5*cm]),
            Table([_kpi_cell(str(n_partial),   "Parciais",  C_AMBER)],   colWidths=[3.5*cm]),
            Table([_kpi_cell(str(n_noncomp),   "Não conf.", C_RED)],     colWidths=[3.5*cm]),
            Table([_kpi_cell(str(n_na),        "N/A (op.)", C_GRAY)],    colWidths=[3.5*cm]),
        ]],
        colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm],
    )
    kpi_table.setStyle(TableStyle([
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND",  (0, 0), (-1, -1), C_NAVY_LIGHT),
        ("ROUNDEDCORNERS", [6]),
        ("TOPPADDING",  (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.7 * cm))

    # ── Matrix by module ──────────────────────────────────────────────────────

    groups = _group_by_module(results)

    module_style = ParagraphStyle(
        "module",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=C_WHITE,
        spaceBefore=12,
        spaceAfter=4,
    )
    req_title_style = ParagraphStyle(
        "req_title",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        textColor=C_TEXT,
        leading=11,
    )
    detail_style = ParagraphStyle(
        "detail",
        fontName="Helvetica",
        fontSize=7.5,
        textColor=C_TEXT2,
        leading=10,
    )
    note_style = ParagraphStyle(
        "note",
        fontName="Helvetica-Oblique",
        fontSize=7,
        textColor=C_TEXT2,
        leading=9,
        leftIndent=6,
    )

    COL_WIDTHS = [3.2*cm, 8.8*cm, 2.4*cm, 1.6*cm]  # ID | Requirement | Status | Score
    FULL_W = sum(COL_WIDTHS)

    for module_name, reqs in groups.items():
        # Module header
        mod_header = Table(
            [[Paragraph(module_name.upper(), module_style)]],
            colWidths=[FULL_W],
        )
        mod_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_NAVY),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(KeepTogether([mod_header, Spacer(1, 1)]))

        # Column header
        col_header = Table(
            [[
                Paragraph('<font size="7" color="#475569"><b>ID</b></font>',
                          ParagraphStyle("ch", alignment=TA_LEFT)),
                Paragraph('<font size="7" color="#475569"><b>REQUISITO</b></font>',
                          ParagraphStyle("ch", alignment=TA_LEFT)),
                Paragraph('<font size="7" color="#475569"><b>STATUS</b></font>',
                          ParagraphStyle("ch", alignment=TA_CENTER)),
                Paragraph('<font size="7" color="#475569"><b>SCORE</b></font>',
                          ParagraphStyle("ch", alignment=TA_CENTER)),
            ]],
            colWidths=COL_WIDTHS,
        )
        col_header.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("LINEBELOW",    (0, 0), (-1, -1), 0.5, C_BORDER),
        ]))
        story.append(col_header)

        # Requirement rows
        for req in reqs:
            status = req.get("status", "")
            lbl, fg, bg = STATUS_CONFIG.get(status, ("?", C_GRAY, C_GRAY_BG))
            score_txt = _score_str(req)
            score_color = _score_color(req)

            req_id = req.get("requirement_id", "")
            title  = req.get("title", req.get("requirement_name", ""))

            # Notes
            notes = _clean_notes(req.get("notes"))
            gap   = (req.get("gap") or "").strip()
            if gap in GENERIC_MESSAGES: gap = ""

            # Build detail cell content
            detail_parts = []
            if gap:
                detail_parts.append(Paragraph(f"<b>Gap:</b> {gap}", note_style))
            for n in notes[:2]:
                detail_parts.append(Paragraph(f"• {n}", note_style))

            req_cell = [Paragraph(title, req_title_style)] + detail_parts

            # Status badge cell
            status_para = Paragraph(
                f'<font size="7.5" color="{fg.hexval()}"><b>{lbl}</b></font>',
                ParagraphStyle("sb", alignment=TA_CENTER, leading=9),
            )

            # Score cell
            score_para = Paragraph(
                f'<font size="9" color="{score_color.hexval()}"><b>{score_txt}</b></font>',
                ParagraphStyle("sc", alignment=TA_CENTER),
            )

            row_data = [[
                Paragraph(f'<font size="8" color="{C_NAVY.hexval()}"><b>{req_id}</b></font>',
                          ParagraphStyle("rid", leading=10)),
                req_cell,
                status_para,
                score_para,
            ]]

            row_table = Table(row_data, colWidths=COL_WIDTHS)
            row_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), bg),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("ALIGN",         (2, 0), (3, 0), "CENTER"),
                ("VALIGN",        (2, 0), (3, 0), "MIDDLE"),
                ("LINEBELOW",     (0, 0), (-1, -1), 0.3, C_BORDER),
                ("LEFTBORDERPADDING", (0, 0), (0, -1), 0),
                # Left accent bar by status color
                ("LINEBEFORE", (0, 0), (0, -1), 3, fg),
            ]))
            story.append(row_table)

        story.append(Spacer(1, 0.4 * cm))

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.2 * cm))
    footer_note = ParagraphStyle(
        "footer_note", fontName="Helvetica-Oblique", fontSize=7, textColor=C_GRAY
    )
    story.append(Paragraph(
        "Este relatório foi gerado automaticamente pelo motor determinístico CO2mply. "
        "Os resultados refletem a análise dos documentos do projeto contra os critérios do protocolo selecionado. "
        "Documento confidencial — para uso exclusivo do proponente do projeto.",
        footer_note,
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(
        story,
        onFirstPage=hf.on_page,
        onLaterPages=hf.on_page,
    )
    return buffer.getvalue()
