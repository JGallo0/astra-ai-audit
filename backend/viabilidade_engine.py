"""
Co2mply — Motor de Viabilidade Financeira
Versão generalizada do bcne_model.py: feedstock como input direto (t/ano).
100% determinístico — zero LLM.
"""
from __future__ import annotations
import dataclasses
from dataclasses import dataclass, field
from math import isfinite
from typing import Optional


# ── Ranges de mercado para validação ──────────────────────────────────────────

MARKET_RANGES: dict = {
    "preco_credito_usd": {
        "min": 30, "max": 300,
        "warn_low": 60, "warn_high": 220,
        "median": 138,
        "label": "Preço do crédito (USD/tCO₂)",
        "fonte": "Puro.earth / Isometric 2024",
    },
    "preco_biochar_brl": {
        "min": 0, "max": 5000,
        "warn_high": 2500,
        "median": 1200,
        "label": "Preço do biochar (BRL/t)",
        "fonte": "Mercado agrícola BR 2024",
    },
    "yield_pirolise": {
        "min": 0.10, "max": 0.50,
        "warn_low": 0.18, "warn_high": 0.42,
        "median": 0.28,
        "label": "Rendimento de pirólise",
        "fonte": "Literatura técnica biochar",
    },
    "fator_carbono": {
        "min": 1.0, "max": 4.0,
        "warn_low": 1.8, "warn_high": 3.3,
        "median": 2.5,
        "label": "Fator de carbono (tCO₂/t biochar)",
        "fonte": "Isometric / Puro.earth protocols",
    },
    "wacc": {
        "min": 0.05, "max": 0.30,
        "warn_low": 0.08, "warn_high": 0.22,
        "median": 0.12,
        "label": "WACC / Taxa de desconto",
        "fonte": "Referência projetos CDR Brasil",
    },
}


def validate_premissas(p: dict) -> list[dict]:
    """Retorna lista de warnings para campos fora do range de mercado."""
    warnings = []
    for field_name, cfg in MARKET_RANGES.items():
        val = p.get(field_name)
        if val is None:
            continue
        if val < cfg.get("warn_low", cfg["min"]):
            warnings.append({
                "field": field_name,
                "label": cfg["label"],
                "value": val,
                "type": "low",
                "message": f"Abaixo do range típico de mercado ({cfg.get('warn_low', cfg['min'])}–{cfg.get('warn_high', cfg['max'])}). Mediana: {cfg['median']}. Fonte: {cfg.get('fonte', '')}.",
            })
        elif val > cfg.get("warn_high", cfg["max"]):
            warnings.append({
                "field": field_name,
                "label": cfg["label"],
                "value": val,
                "type": "high",
                "message": f"Acima do range típico de mercado ({cfg.get('warn_low', cfg['min'])}–{cfg.get('warn_high', cfg['max'])}). Mediana: {cfg['median']}. Fonte: {cfg.get('fonte', '')}.",
            })
    return warnings


# ── Dataclass de premissas ────────────────────────────────────────────────────

@dataclass
class PremissasViabilidade:
    # Produção
    feedstock_t_ano: float = 5_000.0
    yield_pirolise: float = 0.28
    fator_carbono: float = 2.50

    # Receitas
    preco_credito_usd: float = 120.0
    fx_brl_usd: float = 5.70
    preco_biochar_brl: float = 0.0
    escalacao_carbono: float = 0.0
    escalacao_fx: float = 0.0

    # Custos
    capex_total_brl: float = 5_500_000.0
    opex_anual_brl: float = 1_200_000.0
    escalacao_opex: float = 0.0
    vida_util_anos: int = 20

    # Financeiro
    wacc: float = 0.12
    regime_tributario: str = "LP"
    horizonte_anos: int = 20
    ano_investimento: int = 2026

    # Parâmetros tributários LP
    presuncao_irpj: float = 0.08
    presuncao_csll: float = 0.12
    aliquota_ir: float = 0.15
    adicional_ir: float = 0.10
    aliquota_csll: float = 0.09
    limite_adicional_ir_brl: float = 240_000.0
    limite_compensacao_prejuizo: float = 0.30


# ── Engine ────────────────────────────────────────────────────────────────────

def _safe_irr(cash_flows: list) -> Optional[float]:
    def npv(r):
        return sum(cf / (1 + r) ** i for i, cf in enumerate(cash_flows))
    lo, hi = -0.99, 10.0
    nlo, nhi = npv(lo), npv(hi)
    if nlo * nhi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        v = npv(mid)
        if abs(v) < 1e-9:
            break
        if nlo * v <= 0:
            hi = mid
        else:
            lo = mid
            nlo = v
    r = (lo + hi) / 2
    return r if isfinite(r) else None


def _fcl(p: PremissasViabilidade, preco_override: Optional[float] = None) -> list:
    preco = preco_override if preco_override is not None else p.preco_credito_usd
    biochar = p.feedstock_t_ano * p.yield_pirolise
    creditos = biochar * p.fator_carbono
    da = p.capex_total_brl / max(p.vida_util_anos, 1)
    flows = [-p.capex_total_brl]
    prejuizo = 0.0

    for ano in range(1, p.horizonte_anos + 1):
        ec = (1 + p.escalacao_carbono) ** (ano - 1)
        ef = (1 + p.escalacao_fx) ** (ano - 1)
        eo = (1 + p.escalacao_opex) ** (ano - 1)
        rec = creditos * preco * ec * p.fx_brl_usd * ef + biochar * p.preco_biochar_brl
        opex = p.opex_anual_brl * eo
        ebitda = rec - opex
        ebit = ebitda - da

        if p.regime_tributario == "LP":
            base_ir = rec * p.presuncao_irpj
            irpj = base_ir * p.aliquota_ir + max(base_ir - p.limite_adicional_ir_brl, 0) * p.adicional_ir
            csll = rec * p.presuncao_csll * p.aliquota_csll
            trib = irpj + csll
        else:
            comp = min(prejuizo, max(ebit, 0) * p.limite_compensacao_prejuizo)
            base = max(ebit - comp, 0)
            irpj = base * p.aliquota_ir + max(base - p.limite_adicional_ir_brl, 0) * p.adicional_ir
            csll = base * p.aliquota_csll
            trib = irpj + csll
            prejuizo = max(prejuizo - comp, 0) + max(-ebit, 0)

        flows.append(ebit - trib + da)

    return flows


def _breakeven(p: PremissasViabilidade) -> Optional[float]:
    """Menor preço de crédito (USD) para IRR ≥ WACC."""
    lo, hi = 0.0, 600.0
    if (_safe_irr(_fcl(p, hi)) or -1) < p.wacc:
        return None
    if (_safe_irr(_fcl(p, lo)) or -1) >= p.wacc:
        return 0.0
    for _ in range(80):
        mid = (lo + hi) / 2
        irr_m = _safe_irr(_fcl(p, mid)) or -1
        if irr_m >= p.wacc:
            hi = mid
        else:
            lo = mid
        if hi - lo < 0.20:
            break
    return round((lo + hi) / 2, 1)


def calcular_viabilidade(p: PremissasViabilidade) -> dict:
    """Calcula todos os indicadores. Determinístico."""
    biochar = p.feedstock_t_ano * p.yield_pirolise
    creditos = biochar * p.fator_carbono
    da = p.capex_total_brl / max(p.vida_util_anos, 1)

    flows = _fcl(p)
    irr = _safe_irr(flows)
    npv = sum(cf / (1 + p.wacc) ** i for i, cf in enumerate(flows))

    # Payback
    payback_year = None
    cum = 0.0
    for i, cf in enumerate(flows):
        cum += cf
        if i > 0 and cum >= 0:
            payback_year = p.ano_investimento + i
            break

    # FCL acumulado (inclui ano 0 = -capex)
    acumulado, s = [], 0.0
    for cf in flows:
        s += cf
        acumulado.append(round(s, 0))

    # Adicionalidade
    flows_sc = _fcl(p, preco_override=0.0)
    irr_sc = _safe_irr(flows_sc)

    # Receita ano 1
    rec_yr1 = creditos * p.preco_credito_usd * p.fx_brl_usd + biochar * p.preco_biochar_brl
    ebitda_yr1 = rec_yr1 - p.opex_anual_brl

    # Sensibilidade
    sensibilidade = []
    for price in range(30, 271, 10):
        f2 = _fcl(p, preco_override=float(price))
        irr2 = _safe_irr(f2)
        npv2 = sum(cf / (1 + p.wacc) ** i for i, cf in enumerate(f2))
        sensibilidade.append({
            "preco_usd": price,
            "irr": round(irr2 * 100, 2) if irr2 is not None else None,
            "npv_brl": round(npv2, 0),
        })

    return {
        "biochar_t_ano": round(biochar, 1),
        "creditos_tco2_ano": round(creditos, 1),
        "irr": round(irr * 100, 2) if irr is not None else None,
        "npv_brl": round(npv, 0),
        "payback_year": payback_year,
        "ebitda_yr1": round(ebitda_yr1, 0),
        "receita_bruta_yr1": round(rec_yr1, 0),
        "opex_yr1": round(p.opex_anual_brl, 0),
        "margem_ebitda_pct": round(ebitda_yr1 / rec_yr1 * 100, 1) if rec_yr1 > 0 else None,
        "da_anual": round(da, 0),
        "irr_sem_carbono": round(irr_sc * 100, 2) if irr_sc is not None else None,
        "adicionalidade_financeira": irr_sc is None or irr_sc < p.wacc,
        "preco_breakeven_usd": _breakeven(p),
        "fcl_anual": [round(v, 0) for v in flows],
        "fcl_acumulado": acumulado,
        "anos": list(range(p.ano_investimento, p.ano_investimento + p.horizonte_anos + 1)),
        "sensibilidade": sensibilidade,
    }


def premissas_from_dict(d: dict) -> PremissasViabilidade:
    """Constrói PremissasViabilidade ignorando chaves desconhecidas."""
    fields = {f.name for f in dataclasses.fields(PremissasViabilidade)}
    return PremissasViabilidade(**{k: v for k, v in d.items() if k in fields and v is not None})
