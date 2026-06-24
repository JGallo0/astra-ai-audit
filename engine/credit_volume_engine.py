"""
Co2mply — Motor de Estimativa de Volume de Créditos de Carbono (Biochar)

Calcula a quantidade de créditos (tCO₂e/ano) que um projeto de biochar
geraria sob cada metodologia, replicando a abordagem do Module 1 do
Sylvera Biochar Methodology Assessment (2025).

Fórmula central:
  Net CO₂ = Gross CO₂ − E_sourcing − E_processing − E_infrastructure
             − E_biochar_use − E_counter_leakage − Buffer

Referências:
  Woolf et al. (2021) — "Biochar stability and carbon sequestration"
  Sylvera Biochar Methodology Assessment (Oct 2025)
  Isometric Biochar v1.2, Puro.earth Edition 2025, Verra VM0044 v1.2
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional


# ── Constante molecular ───────────────────────────────────────────────────────
CO2_C_RATIO = 44.0 / 12.0   # 3.667 — peso molecular CO₂ / C

# ── Buffer pools por metodologia ─────────────────────────────────────────────
BUFFER_POOL_PCT = {
    "isometric":  0.02,   # 2% — Isometric Standard
    "puro_earth": 0.02,   # 2% — Puro.earth (solo)
    "verra_vcs":  0.05,   # 5% — VCS AFOLU buffer
    "rainbow":    0.03,   # estimado
    "c_sink":     0.03,   # estimado
}

# ── Parâmetros do modelo de permanência (Woolf 2021, calibrado ao Sylvera) ────
# Modelo: log(k) = alpha + beta*MAST + gamma*H/Corg
# k = taxa de decaimento (yr^-1)
# Calibrado para: MAST=20°C, H/Corg=0.200 → Isometric f200=0.90, Puro f200=0.81
_WOOLF = {
    "isometric":  {"alpha": -9.487, "beta": 0.069, "gamma": 2.8},  # 17° percentil (conservador)
    "puro_earth": {"alpha": -8.785, "beta": 0.069, "gamma": 2.8},  # mediana
}

# ── Infraestrutura: excluída por metodologia ──────────────────────────────────
# Puro.earth exclui emissões embodied de infraestrutura do LCA
# Isometric e Verra incluem (amortizado sobre vida do projeto)
INCLUDES_INFRASTRUCTURE = {
    "isometric":  True,
    "puro_earth": False,   # Clarificação Puro — infraestrutura fora do escopo
    "verra_vcs":  True,
    "rainbow":    True,
    "c_sink":     True,
}

# ── Fatores de emissão por padrão (Ecoinvent 3.10 / literatura) ───────────────
EF_TRUCK_TCO2_PER_T_KM = 0.000062   # tCO₂/t·km (caminhão diesel)
EF_DIESEL_TCO2_PER_L   = 0.00269    # tCO₂/L diesel

# Emissões embodied de infraestrutura industrial
# (tCO₂ por USD 1.000 de CAPEX — Ecoinvent Brasil/global)
EF_INFRASTRUCTURE_TCO2_PER_KUSD = 1.60   # ~1,6 tCO₂/k$ (range: 0.8–2.5)

# Fator de emissão elétrica por país (tCO₂/MWh)
ELECTRICITY_FACTORS = {
    "brazil":   0.082,   # SIN 2024 — matriz predominantemente hídrica
    "eu":       0.300,
    "usa":      0.380,
    "global":   0.490,
    "default":  0.300,
}


# ── Inputs do projeto ─────────────────────────────────────────────────────────

@dataclass
class CreditVolumeInputs:
    """
    Parâmetros para cálculo de volume de créditos por metodologia.

    Valores mínimos obrigatórios:
      - biochar_t_dry_year: produção anual de biochar (base seca)
      - carbon_fraction: fração de carbono total no biochar (ex: 0.75)
      - h_c_ratio: razão molar H/Corg (< 0.5 para elegibilidade)

    Valores com bons defaults:
      - mast_celsius: temperatura média do solo (preenchido via Copernicus)
      - feedstock_t_year: automático = biochar / yield_pirolise
    """
    # Produção (obrigatórios)
    biochar_t_dry_year:    float          # t biochar seco / ano
    carbon_fraction:       float = 0.75   # fração de C total no biochar (medição lab)
    h_c_ratio:             float = 0.35   # H/Corg molar ratio (< 0.5 elegível)
    o_c_ratio:             float = 0.15   # O/Corg (< 0.2 elegível)

    # Permanência
    mast_celsius:          float = 20.0   # temperatura média anual do solo (°C)
    pyrolysis_temp_celsius: float = 500.0  # temperatura de pirólise (para Verra)

    # LCA — fontes de emissão
    feedstock_t_year:      float = 0.0    # t feedstock/ano (calculado automaticamente se 0)
    feedstock_yield:       float = 0.28   # yield de pirólise (para estimar feedstock)
    transport_km_feedstock: float = 30.0  # km coleta → planta
    energy_kwh_t_biochar:  float = 174.0  # kWh/t biochar produzido
    transport_km_biochar:  float = 50.0   # km planta → aplicação
    capex_usd:             float = 0.0    # CAPEX total em USD
    project_life_years:    int   = 20
    country_electricity:   str   = "brazil"

    # Counterfactual / leakage
    counterfactual_tco2_per_t_feedstock: float = 0.0  # default 0 para resíduos

    # Metodologias a calcular
    methodologies: list = field(
        default_factory=lambda: ["isometric", "puro_earth", "verra_vcs"]
    )


# ── Funções de permanência ────────────────────────────────────────────────────

def permanence_factor_200yr(
    mast_celsius: float,
    h_c_ratio: float,
    methodology: str = "isometric",
) -> float:
    """
    Fator de permanência Woolf 2021 para opção 200 anos.
    Isometric usa 17° percentil (conservador); Puro usa mediana.
    Calibrado para: MAST=20°C, H/Corg=0.200 → Iso=0.90, Puro=0.81.
    """
    params = _WOOLF.get(methodology, _WOOLF["puro_earth"])
    log_k = params["alpha"] + params["beta"] * mast_celsius + params["gamma"] * h_c_ratio
    k = math.exp(log_k)
    f = math.exp(-k * 200)
    return max(0.0, min(1.0, f))


def permanence_factor_verra(pyrolysis_temp_celsius: float) -> float:
    """
    Fator de permanência Verra VM0044 — baseado em temperatura de pirólise.
    Verra usa lookup table simplificada (não Woolf).
    """
    if pyrolysis_temp_celsius >= 700:
        return 0.92
    elif pyrolysis_temp_celsius >= 600:
        return 0.89
    elif pyrolysis_temp_celsius >= 450:
        return 0.80
    else:
        return 0.70


def get_permanence_factor(inputs: CreditVolumeInputs, methodology: str) -> float:
    """Retorna o fator de permanência correto por metodologia."""
    if methodology == "verra_vcs":
        return permanence_factor_verra(inputs.pyrolysis_temp_celsius)
    else:
        return permanence_factor_200yr(inputs.mast_celsius, inputs.h_c_ratio, methodology)


# ── Cálculo de emissões LCA ───────────────────────────────────────────────────

def calc_lca_emissions(inputs: CreditVolumeInputs, methodology: str) -> dict:
    """
    Calcula cada componente de emissão do LCA (tCO₂/ano).
    Retorna dict com linha de cada componente.
    """
    feedstock = inputs.feedstock_t_year or (inputs.biochar_t_dry_year / max(inputs.feedstock_yield, 0.01))
    biochar   = inputs.biochar_t_dry_year
    ef_elec   = ELECTRICITY_FACTORS.get(inputs.country_electricity, ELECTRICITY_FACTORS["default"])

    # A1/A2: Biomass sourcing (coleta + transporte do feedstock)
    e_sourcing = feedstock * inputs.transport_km_feedstock * EF_TRUCK_TCO2_PER_T_KM

    # A3: Biomass processing (energia elétrica na planta)
    e_processing = biochar * inputs.energy_kwh_t_biochar * ef_elec / 1000  # kWh → MWh

    # A4: Infrastructure (embodied emissions amortizadas)
    if INCLUDES_INFRASTRUCTURE.get(methodology, True) and inputs.capex_usd > 0:
        total_embodied = inputs.capex_usd / 1000 * EF_INFRASTRUCTURE_TCO2_PER_KUSD
        e_infrastructure = total_embodied / max(inputs.project_life_years, 1)
    else:
        e_infrastructure = 0.0

    # B1: Biochar use (transporte + aplicação)
    e_biochar_use = biochar * inputs.transport_km_biochar * EF_TRUCK_TCO2_PER_T_KM

    # Counterfactual / leakage
    e_counter_leakage = feedstock * inputs.counterfactual_tco2_per_t_feedstock

    return {
        "e_sourcing":        round(e_sourcing, 1),
        "e_processing":      round(e_processing, 1),
        "e_infrastructure":  round(e_infrastructure, 1),
        "e_biochar_use":     round(e_biochar_use, 1),
        "e_counter_leakage": round(e_counter_leakage, 1),
    }


# ── Cálculo principal ─────────────────────────────────────────────────────────

def calc_credit_volume(inputs: CreditVolumeInputs, methodology: str) -> dict:
    """
    Calcula o volume de créditos para uma metodologia específica.

    Returns dict com:
      gross_co2, emissions (por linha), buffer, net_co2, permanence_factor,
      corc_factor (tCO₂/t biochar)
    """
    # Fator de permanência
    perm = get_permanence_factor(inputs, methodology)

    # Remoção bruta = biochar × C_fraction × (44/12) × permanência
    gross = inputs.biochar_t_dry_year * inputs.carbon_fraction * CO2_C_RATIO * perm

    # LCA
    emissions = calc_lca_emissions(inputs, methodology)
    total_emissions = sum(emissions.values())

    # Buffer pool
    buffer_pct = BUFFER_POOL_PCT.get(methodology, 0.02)
    buffer = gross * buffer_pct

    # Remoção líquida
    net = gross - total_emissions - buffer

    # CORC factor (tCO₂/t biochar seco — para comparação com auditorias reais)
    corc_factor = net / inputs.biochar_t_dry_year if inputs.biochar_t_dry_year > 0 else 0.0

    return {
        "methodology":       methodology,
        "permanence_factor": round(perm, 3),
        "gross_co2":         round(gross, 0),
        "e_sourcing":        -round(emissions["e_sourcing"], 0),
        "e_processing":      -round(emissions["e_processing"], 0),
        "e_infrastructure":  -round(emissions["e_infrastructure"], 0),
        "e_biochar_use":     -round(emissions["e_biochar_use"], 0),
        "e_counter_leakage": -round(emissions["e_counter_leakage"], 0),
        "buffer_pool":       -round(buffer, 0),
        "buffer_pct":        buffer_pct,
        "net_co2_year":      round(net, 0),
        "net_co2_20yr":      round(net * 20, 0),
        "corc_factor":       round(corc_factor, 3),
        "includes_infrastructure": INCLUDES_INFRASTRUCTURE.get(methodology, True),
    }


def compare_methodologies(inputs: CreditVolumeInputs) -> dict:
    """
    Calcula e compara o volume de créditos para todas as metodologias configuradas.

    Returns:
      {
        "inputs_summary": {...},
        "results": {
          "isometric": {...},
          "puro_earth": {...},
          "verra_vcs": {...},
        },
        "comparison": {
          "max_method": "isometric",
          "min_method": "puro_earth",
          "spread_pct": 10.6,
          "annual_average": 2054,
          "cumulative_20yr_average": 41080,
        }
      }
    """
    results = {}
    for method in inputs.methodologies:
        try:
            results[method] = calc_credit_volume(inputs, method)
        except Exception as e:
            results[method] = {"error": str(e), "net_co2_year": 0}

    # Comparativo
    nets = {m: r.get("net_co2_year", 0) for m, r in results.items() if "error" not in r}
    if nets:
        max_m = max(nets, key=nets.get)
        min_m = min(nets, key=nets.get)
        avg   = sum(nets.values()) / len(nets)
        spread = (nets[max_m] - nets[min_m]) / avg * 100 if avg > 0 else 0
    else:
        max_m = min_m = None
        avg = spread = 0

    # Feedstock estimado
    feedstock_est = inputs.feedstock_t_year or (inputs.biochar_t_dry_year / max(inputs.feedstock_yield, 0.01))

    return {
        "inputs_summary": {
            "biochar_t_dry_year":    inputs.biochar_t_dry_year,
            "carbon_fraction":       inputs.carbon_fraction,
            "h_c_ratio":             inputs.h_c_ratio,
            "o_c_ratio":             inputs.o_c_ratio,
            "mast_celsius":          inputs.mast_celsius,
            "pyrolysis_temp_celsius": inputs.pyrolysis_temp_celsius,
            "feedstock_t_year":      round(feedstock_est, 0),
            "project_life_years":    inputs.project_life_years,
            "capex_usd":             inputs.capex_usd,
        },
        "results": results,
        "comparison": {
            "max_method":             max_m,
            "min_method":             min_m,
            "spread_pct":             round(spread, 1),
            "annual_average_net":     round(avg, 0),
            "cumulative_20yr_average": round(avg * 20, 0),
            "net_by_method":          {m: round(v, 0) for m, v in nets.items()},
        },
    }


# ── Helpers para integração com Viabilidade ───────────────────────────────────

def inputs_from_viabilidade(premissas: dict, profile_or_climate: dict = None) -> CreditVolumeInputs:
    """
    Constrói CreditVolumeInputs a partir das premissas de Viabilidade.
    Integra automaticamente MAST do Copernicus C3S se disponível.
    """
    biochar = (premissas.get("feedstock_t_ano", 5000)
               * premissas.get("yield_pirolise", 0.28))

    # MAST: preferir dado real do Copernicus, senão usar default por localização
    mast = 20.0  # default tropical
    if profile_or_climate:
        t = profile_or_climate.get("temperature") or {}
        c3s_temp = t.get("c3s_temp")
        if c3s_temp is not None:
            mast = float(c3s_temp)

    # CAPEX em USD (convertendo da moeda do projeto)
    capex_proj = premissas.get("capex_total", 0) or 0
    fx = premissas.get("fx_rate", 5.70) or 5.70
    moeda = premissas.get("moeda_projeto", "BRL")
    capex_usd = capex_proj / fx if moeda != "USD" else capex_proj

    # País para fator de emissão elétrica
    country_electricity = "brazil"  # default — melhorar com project_country futuramente

    return CreditVolumeInputs(
        biochar_t_dry_year=round(biochar, 1),
        carbon_fraction=0.75,          # default — idealmente vem de análise lab
        h_c_ratio=0.35,                # default — idealmente do projeto
        o_c_ratio=0.15,                # default
        mast_celsius=mast,
        feedstock_t_year=premissas.get("feedstock_t_ano", 0),
        feedstock_yield=premissas.get("yield_pirolise", 0.28),
        energy_kwh_t_biochar=174.0,    # BCNE reference
        capex_usd=capex_usd,
        project_life_years=premissas.get("horizonte_anos", 20),
        country_electricity=country_electricity,
    )
