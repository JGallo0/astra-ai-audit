"""
Co2mply — Motor de Viabilidade Financeira
Versão generalizada: feedstock como input direto (t/ano), multi-moeda.
100% determinístico — zero LLM.
"""
from __future__ import annotations
import dataclasses
from dataclasses import dataclass
from math import isfinite
from typing import Optional


# ── Moedas suportadas ─────────────────────────────────────────────────────────

MOEDAS = {
    "BRL": {"label": "BRL — Real Brasileiro",        "symbol": "R$",   "fx_default": 5.70},
    "USD": {"label": "USD — Dólar Americano",         "symbol": "$",    "fx_default": 1.0},
    "EUR": {"label": "EUR — Euro",                    "symbol": "€",    "fx_default": 0.92},
    "GBP": {"label": "GBP — Libra Esterlina",         "symbol": "£",    "fx_default": 0.79},
    "CLP": {"label": "CLP — Peso Chileno",            "symbol": "CLP$", "fx_default": 940.0},
    "COP": {"label": "COP — Peso Colombiano",         "symbol": "COP$", "fx_default": 4100.0},
    "MXN": {"label": "MXN — Peso Mexicano",           "symbol": "MX$",  "fx_default": 17.5},
    "DKK": {"label": "DKK — Coroa Dinamarquesa",      "symbol": "kr",   "fx_default": 6.9},
    "SEK": {"label": "SEK — Coroa Sueca",             "symbol": "kr",   "fx_default": 10.4},
    "NOK": {"label": "NOK — Coroa Norueguesa",        "symbol": "kr",   "fx_default": 10.6},
    "JPY": {"label": "JPY — Iene Japonês",            "symbol": "¥",    "fx_default": 155.0},
    "AUD": {"label": "AUD — Dólar Australiano",       "symbol": "A$",   "fx_default": 1.55},
    "CAD": {"label": "CAD — Dólar Canadense",         "symbol": "C$",   "fx_default": 1.36},
    "ZAR": {"label": "ZAR — Rand Sul-Africano",       "symbol": "R",    "fx_default": 18.5},
    "INR": {"label": "INR — Rúpia Indiana",           "symbol": "₹",   "fx_default": 83.0},
}


# ── Ranges de mercado ─────────────────────────────────────────────────────────

MARKET_RANGES: dict = {
    "preco_credito_usd": {
        "min": 30, "max": 300,
        "warn_low": 60, "warn_high": 220,
        "median": 138,
        "label": "Preço do crédito (USD/tCO₂)",
        "fonte": "Puro.earth / Isometric 2024",
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
        "fonte": "Referência projetos CDR globais",
    },
    "aliquota_efetiva_ir": {
        "min": 0.0, "max": 0.45,
        "warn_low": 0.05, "warn_high": 0.38,
        "median": 0.22,
        "label": "Alíquota efetiva de IR",
        "fonte": "Referência OCDE — varia por país/regime",
    },
}


def validate_premissas(p: dict) -> list[dict]:
    warnings = []
    for field_name, cfg in MARKET_RANGES.items():
        val = p.get(field_name)
        if val is None:
            continue
        lo = cfg.get("warn_low", cfg["min"])
        hi = cfg.get("warn_high", cfg["max"])
        if val < lo:
            warnings.append({
                "field": field_name, "label": cfg["label"], "value": val, "type": "low",
                "message": f"Abaixo do range típico ({lo}–{hi}). Mediana: {cfg['median']}. Fonte: {cfg.get('fonte', '')}.",
            })
        elif val > hi:
            warnings.append({
                "field": field_name, "label": cfg["label"], "value": val, "type": "high",
                "message": f"Acima do range típico ({lo}–{hi}). Mediana: {cfg['median']}. Fonte: {cfg.get('fonte', '')}.",
            })
    return warnings


# ── Dataclass de premissas ────────────────────────────────────────────────────

@dataclass
class PremissasViabilidade:
    # Moeda
    moeda_projeto:  str   = "BRL"       # código ISO 4217
    moeda_credito:  str   = "USD"       # créditos de carbono — sempre USD

    # Produção
    feedstock_t_ano: float = 5_000.0
    yield_pirolise:  float = 0.28
    fator_carbono:   float = 2.50

    # Receitas (monetários em moeda_projeto, exceto preco_credito_usd que é sempre USD)
    preco_credito_usd: float = 120.0
    fx_rate:           float = 5.70    # moeda_credito → moeda_projeto (1.0 se igual)
    preco_biochar:     float = 0.0     # em moeda_projeto / t biochar
    escalacao_carbono: float = 0.0
    escalacao_fx:      float = 0.0

    # Custos (em moeda_projeto)
    capex_total:    float = 5_500_000.0
    opex_anual:     float = 1_200_000.0
    escalacao_opex: float = 0.0
    vida_util_anos: int   = 20

    # Financeiro
    wacc:                float = 0.12
    aliquota_efetiva_ir: float = 0.20   # fração (0.20 = 20%)
    horizonte_anos:      int   = 20
    ano_investimento:    int   = 2026


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
    biochar  = p.feedstock_t_ano * p.yield_pirolise
    creditos = biochar * p.fator_carbono
    da       = p.capex_total / max(p.vida_util_anos, 1)
    flows    = [-p.capex_total]

    for ano in range(1, p.horizonte_anos + 1):
        ec = (1 + p.escalacao_carbono) ** (ano - 1)
        ef = (1 + p.escalacao_fx)      ** (ano - 1)
        eo = (1 + p.escalacao_opex)    ** (ano - 1)
        rec   = creditos * preco * ec * p.fx_rate * ef + biochar * p.preco_biochar
        opex  = p.opex_anual * eo
        ebitda = rec - opex
        ebit   = ebitda - da
        trib   = max(ebit, 0.0) * p.aliquota_efetiva_ir
        flows.append(ebit - trib + da)

    return flows


def _breakeven(p: PremissasViabilidade) -> Optional[float]:
    lo, hi = 0.0, 600.0
    if (_safe_irr(_fcl(p, hi)) or -1) < p.wacc:
        return None
    if (_safe_irr(_fcl(p, lo)) or -1) >= p.wacc:
        return 0.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if (_safe_irr(_fcl(p, mid)) or -1) >= p.wacc:
            hi = mid
        else:
            lo = mid
        if hi - lo < 0.20:
            break
    return round((lo + hi) / 2, 1)


def calcular_viabilidade(p: PremissasViabilidade) -> dict:
    biochar  = p.feedstock_t_ano * p.yield_pirolise
    creditos = biochar * p.fator_carbono
    da       = p.capex_total / max(p.vida_util_anos, 1)

    flows = _fcl(p)
    irr   = _safe_irr(flows)
    npv   = sum(cf / (1 + p.wacc) ** i for i, cf in enumerate(flows))

    payback_year = None
    cum = 0.0
    for i, cf in enumerate(flows):
        cum += cf
        if i > 0 and cum >= 0:
            payback_year = p.ano_investimento + i
            break

    acumulado, s = [], 0.0
    for cf in flows:
        s += cf
        acumulado.append(round(s, 0))

    flows_sc = _fcl(p, preco_override=0.0)
    irr_sc   = _safe_irr(flows_sc)

    rec_yr1    = creditos * p.preco_credito_usd * p.fx_rate + biochar * p.preco_biochar
    ebitda_yr1 = rec_yr1 - p.opex_anual

    sensibilidade = []
    for price in range(30, 271, 10):
        f2   = _fcl(p, preco_override=float(price))
        irr2 = _safe_irr(f2)
        npv2 = sum(cf / (1 + p.wacc) ** i for i, cf in enumerate(f2))
        sensibilidade.append({
            "preco_usd": price,
            "irr": round(irr2 * 100, 2) if irr2 is not None else None,
            "npv":  round(npv2, 0),
        })

    return {
        "moeda_projeto":         p.moeda_projeto,
        "biochar_t_ano":         round(biochar, 1),
        "creditos_tco2_ano":     round(creditos, 1),
        "irr":                   round(irr * 100, 2) if irr is not None else None,
        "npv":                   round(npv, 0),
        "payback_year":          payback_year,
        "ebitda_yr1":            round(ebitda_yr1, 0),
        "receita_bruta_yr1":     round(rec_yr1, 0),
        "opex_yr1":              round(p.opex_anual, 0),
        "margem_ebitda_pct":     round(ebitda_yr1 / rec_yr1 * 100, 1) if rec_yr1 > 0 else None,
        "da_anual":              round(da, 0),
        "irr_sem_carbono":       round(irr_sc * 100, 2) if irr_sc is not None else None,
        "adicionalidade_financeira": irr_sc is None or irr_sc < p.wacc,
        "preco_breakeven_usd":   _breakeven(p),
        "fcl_anual":             [round(v, 0) for v in flows],
        "fcl_acumulado":         acumulado,
        "anos":                  list(range(p.ano_investimento, p.ano_investimento + p.horizonte_anos + 1)),
        "sensibilidade":         sensibilidade,
    }


def premissas_from_dict(d: dict) -> PremissasViabilidade:
    """Constrói PremissasViabilidade com suporte a nomes antigos (backward compat)."""
    aliases = {
        "fx_brl_usd":      "fx_rate",
        "preco_biochar_brl": "preco_biochar",
        "capex_total_brl": "capex_total",
        "opex_anual_brl":  "opex_anual",
    }
    # Aplica aliases
    data = {}
    for k, v in d.items():
        key = aliases.get(k, k)
        data[key] = v

    # Compat: converte regime_tributario → aliquota_efetiva_ir
    if "aliquota_efetiva_ir" not in data and "regime_tributario" in data:
        data["aliquota_efetiva_ir"] = 0.20 if data["regime_tributario"] == "LP" else 0.25

    # Remove campos desconhecidos
    valid = {f.name for f in dataclasses.fields(PremissasViabilidade)}
    return PremissasViabilidade(**{k: v for k, v in data.items() if k in valid and v is not None})
