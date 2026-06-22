"""
Co2mply — Serviços auxiliares do módulo Viabilidade:
  1. Extração de premissas de planilha via LLM
  2. Geração de workbook Excel
"""
from __future__ import annotations
import io
import json
from datetime import datetime
from typing import Any

import pandas as pd


# ── Extração via LLM ──────────────────────────────────────────────────────────

EXTRACTION_SCHEMA = {
    "feedstock_t_ano":    "Toneladas de feedstock/biomassa seca processada por ano (t/ano)",
    "yield_pirolise":     "Rendimento da pirólise em fração decimal (ex: 28% → 0.28)",
    "fator_carbono":      "Fator de carbono: tCO₂e por tonelada de biochar produzido",
    "preco_credito_usd":  "Preço assumido do crédito de carbono em USD por tCO₂e",
    "fx_brl_usd":         "Taxa de câmbio BRL por USD usada no modelo",
    "preco_biochar_brl":  "Preço de venda do biochar em BRL por tonelada (0 se não vendido)",
    "capex_total_brl":    "CAPEX total do projeto em BRL",
    "opex_anual_brl":     "OPEX (custos operacionais) anuais totais em BRL",
    "wacc":               "Taxa de desconto ou WACC em fração decimal (ex: 12% → 0.12)",
    "regime_tributario":  "'LP' para Lucro Presumido ou 'LR' para Lucro Real",
    "horizonte_anos":     "Horizonte do projeto em anos",
    "ano_investimento":   "Ano do investimento inicial (ex: 2026)",
    "escalacao_carbono":  "Escalação anual do preço do carbono em fração (ex: 3% → 0.03)",
    "escalacao_opex":     "Escalação anual do OPEX em fração (ex: 5% → 0.05)",
}


def extract_premissas_from_spreadsheet(
    file_bytes: bytes,
    filename: str,
    openai_client: Any,
    model: str,
) -> dict:
    """
    Lê o arquivo (xlsx/csv), converte para texto e usa LLM para extrair premissas.
    Retorna dict com valores extraídos (None para não encontrados).
    """
    # Lê o arquivo
    try:
        if filename.lower().endswith(".csv"):
            df_dict = {"Principal": pd.read_csv(io.BytesIO(file_bytes))}
        else:
            df_dict = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
    except Exception as e:
        return {"_erro": f"Não foi possível ler o arquivo: {e}"}

    # Converte para texto (até 14k chars)
    parts = []
    for sheet, df in df_dict.items():
        parts.append(f"\n=== Aba: {sheet} ===")
        parts.append(df.head(60).to_string(max_cols=20))
    text = "\n".join(parts)[:14_000]

    schema_text = "\n".join(f'  "{k}": {v}' for k, v in EXTRACTION_SCHEMA.items())

    prompt = f"""Analise esta planilha de modelagem financeira de projeto de biochar e extraia os parâmetros listados.

PLANILHA:
{text}

PARÂMETROS A EXTRAIR:
{{{schema_text}}}

REGRAS:
- Retorne apenas JSON válido, sem markdown
- Use null para campos não encontrados — nunca invente valores
- Valores percentuais devem ser convertidos para fração decimal (28% → 0.28)
- Valores monetários devem estar em BRL (capex, opex) ou USD (preço crédito)
- Se encontrar múltiplos cenários, use o cenário base ou mais conservador"""

    resp = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Especialista em extração de dados financeiros de planilhas. Retorne apenas JSON válido."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    try:
        extracted = json.loads(resp.choices[0].message.content)
    except Exception:
        extracted = {}

    # Remove chaves desconhecidas e normaliza tipos
    valid_keys = set(EXTRACTION_SCHEMA.keys())
    result = {}
    for k, v in extracted.items():
        if k in valid_keys and v is not None:
            result[k] = v

    return result


# ── Geração de Excel ──────────────────────────────────────────────────────────

def _fmt_brl(v):
    if v is None: return "—"
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _fmt_pct(v):
    if v is None: return "—"
    return f"{v:.1f}%"

def _fmt_usd(v):
    if v is None: return "—"
    return f"$ {v:,.0f}".replace(",", ".")


def generate_viabilidade_excel(premissas: dict, resultado: dict, project_name: str) -> bytes:
    """Gera workbook Excel com 5 abas: Premissas, Produção, FCL, Indicadores, Sensibilidade."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import (
            Font, PatternFill, Alignment, Border, Side, numbers
        )
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise RuntimeError("openpyxl não instalado. Adicione ao requirements.txt.")

    NAVY   = "1A3160"
    GREEN  = "16A34A"
    AMBER  = "B45309"
    RED    = "DC2626"
    LGRAY  = "F3F4F6"
    WHITE  = "FFFFFF"

    def hdr_fill(color=NAVY):
        return PatternFill("solid", fgColor=color)

    def hdr_font(bold=True, color=WHITE):
        return Font(bold=bold, color=color, name="Calibri", size=11)

    def data_font(bold=False):
        return Font(bold=bold, name="Calibri", size=10)

    def border():
        s = Side(style="thin", color="D1D5DB")
        return Border(left=s, right=s, top=s, bottom=s)

    def set_row(ws, row, label, value, fmt="text", indent=0):
        c_lbl = ws.cell(row=row, column=1, value=(" " * indent) + label)
        c_lbl.font = data_font()
        c_lbl.fill = PatternFill("solid", fgColor=LGRAY)
        c_lbl.border = border()
        c_lbl.alignment = Alignment(horizontal="left")
        c_val = ws.cell(row=row, column=2, value=value)
        c_val.font = data_font()
        c_val.border = border()
        c_val.alignment = Alignment(horizontal="right")
        if fmt == "brl" and isinstance(value, (int, float)):
            c_val.number_format = '#,##0'
        elif fmt == "pct" and isinstance(value, (int, float)):
            c_val.number_format = '0.00%'
        elif fmt == "usd" and isinstance(value, (int, float)):
            c_val.number_format = '"$"#,##0.00'

    wb = Workbook()
    date_str = datetime.now().strftime("%d/%m/%Y")

    # ── Aba 1: Premissas ──────────────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Premissas"
    ws1.column_dimensions["A"].width = 36
    ws1.column_dimensions["B"].width = 22

    # Título
    ws1.merge_cells("A1:B1")
    c = ws1["A1"]
    c.value = f"Co2mply — Premissas de Viabilidade | {project_name} | {date_str}"
    c.font = Font(bold=True, color=WHITE, name="Calibri", size=13)
    c.fill = hdr_fill(NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 28

    def section(ws, row, title):
        ws.merge_cells(f"A{row}:B{row}")
        c = ws[f"A{row}"]
        c.value = title
        c.font = Font(bold=True, color=WHITE, name="Calibri", size=10)
        c.fill = hdr_fill("374151")
        c.alignment = Alignment(horizontal="left", indent=1)
        ws.row_dimensions[row].height = 20

    r = 2
    section(ws1, r, "PRODUÇÃO"); r += 1
    set_row(ws1, r, "Feedstock (t/ano, base seca)", premissas.get("feedstock_t_ano"), "brl"); r += 1
    set_row(ws1, r, "Rendimento de pirólise", premissas.get("yield_pirolise"), "pct"); r += 1
    set_row(ws1, r, "Fator de carbono (tCO₂/t biochar)", premissas.get("fator_carbono")); r += 1
    set_row(ws1, r, "Biochar produzido (t/ano)", resultado.get("biochar_t_ano"), "brl"); r += 1
    set_row(ws1, r, "Créditos gerados (tCO₂e/ano)", resultado.get("creditos_tco2_ano"), "brl"); r += 1

    section(ws1, r, "RECEITAS"); r += 1
    set_row(ws1, r, "Preço crédito (USD/tCO₂e)", premissas.get("preco_credito_usd"), "usd"); r += 1
    set_row(ws1, r, "Câmbio (BRL/USD)", premissas.get("fx_brl_usd")); r += 1
    set_row(ws1, r, "Preço biochar (BRL/t)", premissas.get("preco_biochar_brl"), "brl"); r += 1
    set_row(ws1, r, "Receita bruta ano 1 (BRL)", resultado.get("receita_bruta_yr1"), "brl"); r += 1

    section(ws1, r, "CUSTOS"); r += 1
    set_row(ws1, r, "CAPEX total (BRL)", premissas.get("capex_total_brl"), "brl"); r += 1
    set_row(ws1, r, "OPEX anual (BRL)", premissas.get("opex_anual_brl"), "brl"); r += 1
    set_row(ws1, r, "Depreciação anual (BRL)", resultado.get("da_anual"), "brl"); r += 1
    set_row(ws1, r, "EBITDA ano 1 (BRL)", resultado.get("ebitda_yr1"), "brl"); r += 1

    section(ws1, r, "FINANCEIRO"); r += 1
    set_row(ws1, r, "WACC / Taxa de desconto", premissas.get("wacc"), "pct"); r += 1
    set_row(ws1, r, "Regime tributário", premissas.get("regime_tributario")); r += 1
    set_row(ws1, r, "Horizonte (anos)", premissas.get("horizonte_anos")); r += 1
    set_row(ws1, r, "Ano de investimento", premissas.get("ano_investimento")); r += 1

    # ── Aba 2: Indicadores ────────────────────────────────────────────────────
    ws2 = wb.create_sheet("Indicadores")
    ws2.column_dimensions["A"].width = 38
    ws2.column_dimensions["B"].width = 22

    ws2.merge_cells("A1:B1")
    c = ws2["A1"]
    c.value = "INDICADORES FINANCEIROS"
    c.font = hdr_font()
    c.fill = hdr_fill(NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 28

    irr = resultado.get("irr")
    irr_sc = resultado.get("irr_sem_carbono")
    wacc_val = premissas.get("wacc", 0.12)

    indicators = [
        ("TIR (IRR)", f"{irr:.1f}%" if irr is not None else "—"),
        ("VPL (NPV)", _fmt_brl(resultado.get("npv_brl"))),
        ("Payback", str(resultado.get("payback_year")) if resultado.get("payback_year") else "Não atingido"),
        ("EBITDA Ano 1", _fmt_brl(resultado.get("ebitda_yr1"))),
        ("Margem EBITDA Ano 1", _fmt_pct(resultado.get("margem_ebitda_pct"))),
        ("—", "—"),
        ("ADICIONALIDADE FINANCEIRA", ""),
        ("TIR sem receita de carbono", f"{irr_sc:.1f}%" if irr_sc is not None else "Inviável"),
        ("Adicionalidade confirmada?", "✓ SIM" if resultado.get("adicionalidade_financeira") else "✗ NÃO"),
        ("—", "—"),
        ("Preço break-even (USD/tCO₂)", _fmt_usd(resultado.get("preco_breakeven_usd"))),
    ]

    for i, (lbl, val) in enumerate(indicators, start=2):
        cl = ws2.cell(row=i, column=1, value=lbl)
        cv = ws2.cell(row=i, column=2, value=val)
        cl.font = Font(bold=lbl in ("ADICIONALIDADE FINANCEIRA",), name="Calibri", size=10)
        cl.fill = PatternFill("solid", fgColor=LGRAY)
        cv.font = Font(bold=True, name="Calibri", size=10)
        for c in (cl, cv):
            c.border = border()
            c.alignment = Alignment(horizontal="right" if c.column == 2 else "left")

    # ── Aba 3: Fluxo de Caixa ─────────────────────────────────────────────────
    ws3 = wb.create_sheet("Fluxo de Caixa")
    ws3.column_dimensions["A"].width = 8
    for col in range(2, 23):
        ws3.column_dimensions[get_column_letter(col)].width = 14

    # Header
    ws3.merge_cells(f"A1:V1")
    c = ws3["A1"]
    c.value = "FLUXO DE CAIXA LIVRE — 20 ANOS (BRL)"
    c.font = hdr_font()
    c.fill = hdr_fill(NAVY)
    c.alignment = Alignment(horizontal="center")
    ws3.row_dimensions[1].height = 24

    fcl = resultado.get("fcl_anual", [])
    acum = resultado.get("fcl_acumulado", [])
    anos = resultado.get("anos", [])

    header_row = ["Ano"] + [str(a) for a in anos]
    for col, val in enumerate(header_row, start=1):
        c = ws3.cell(row=2, column=col, value=val)
        c.font = hdr_font(color=WHITE)
        c.fill = hdr_fill("374151")
        c.alignment = Alignment(horizontal="center")

    fcl_row = ["FCL"] + [float(v) for v in fcl]
    acum_row = ["Acumulado"] + [float(v) for v in acum]

    for col, val in enumerate(fcl_row, start=1):
        c = ws3.cell(row=3, column=col, value=val)
        c.font = data_font()
        c.border = border()
        c.alignment = Alignment(horizontal="right")
        if isinstance(val, float):
            c.number_format = '#,##0'
            c.font = Font(color=RED if val < 0 else GREEN, name="Calibri", size=10)

    for col, val in enumerate(acum_row, start=1):
        c = ws3.cell(row=4, column=col, value=val)
        c.font = data_font()
        c.border = border()
        c.alignment = Alignment(horizontal="right")
        if isinstance(val, float):
            c.number_format = '#,##0'

    # ── Aba 4: Sensibilidade ──────────────────────────────────────────────────
    ws4 = wb.create_sheet("Sensibilidade")
    ws4.column_dimensions["A"].width = 22
    ws4.column_dimensions["B"].width = 14
    ws4.column_dimensions["C"].width = 18

    ws4.merge_cells("A1:C1")
    c = ws4["A1"]
    c.value = "SENSIBILIDADE — Preço do Crédito × TIR / VPL"
    c.font = hdr_font()
    c.fill = hdr_fill(NAVY)
    c.alignment = Alignment(horizontal="center")

    headers = ["Preço Crédito (USD)", "TIR (%)", "VPL (BRL)"]
    for col, h in enumerate(headers, start=1):
        c = ws4.cell(row=2, column=col, value=h)
        c.font = hdr_font(color=WHITE)
        c.fill = hdr_fill("374151")
        c.alignment = Alignment(horizontal="center")

    for row_i, s in enumerate(resultado.get("sensibilidade", []), start=3):
        irr_s = s.get("irr")
        npv_s = s.get("npv_brl")
        vals = [s["preco_usd"], irr_s, npv_s]
        for col, val in enumerate(vals, start=1):
            c = ws4.cell(row=row_i, column=col, value=val)
            c.border = border()
            c.alignment = Alignment(horizontal="right")
            c.font = data_font()
            if col == 2 and irr_s is not None:
                c.font = Font(
                    color=GREEN if irr_s >= (wacc_val * 100) else RED,
                    name="Calibri", size=10
                )
                c.number_format = '0.00'
            if col == 3 and npv_s is not None:
                c.number_format = '#,##0'
                c.font = Font(color=GREEN if npv_s >= 0 else RED, name="Calibri", size=10)
            if col == 1:
                c.number_format = '"$"#,##0'

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
