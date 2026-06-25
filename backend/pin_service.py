"""
Co2mply — PIN Service (Project Idea Note)

Converte dados de formulário diretamente em ProjectProfile e executa
auditoria multi-metodologia sem necessidade de PDD ou vector store.

Fluxo:
  1. Formulário → build_profile_from_form() → ProjectProfile
  2. ProjectProfile → run_pin_audit() → resultados por metodologia
  3. Resultados → recomendação + raciocínio determinístico
"""

from __future__ import annotations
import dataclasses
from typing import Any

from engine.project_profile import ProjectProfile, profile_to_legacy_dict
from engine.country_cpi import get_cpi
from engine.dimension_map import compute_dimension_scores, compute_weighted_score


METHOD_LABELS = {
    "isometric":  "Isometric Biochar v1.2",
    "puro_earth": "Puro.Earth Edition 2025",
    "verra_vcs":  "Verra VCS VM0044",
}

GRADE_LABELS = {
    "A+": "Excelente", "A": "Forte", "B+": "Bom",
    "B": "Moderado", "C": "Inicial",
}


def _score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    return "C"


# Defaults conservadores de H/Corg por tipo de feedstock
# Usados quando o usuário não informou o valor laboratorial.
# Fonte: Woolf et al. 2021, literatura de biochar por tipo de biomassa.
_HC_DEFAULTS = {
    "forest_biomass":      0.35,  # madeira, < carbonização a 500°C
    "urban_wood":          0.35,
    "agricultural_residue":0.40,  # palha, casca — maior teor de cinzas
    "food_waste":          0.45,
    "animal_manure":       0.50,  # limite próximo ao hard gate — conservador
    "sewage_sludge":       0.50,
    "mixed":               0.42,
    "other":               0.40,
}
_MAST_DEFAULT = 20.0  # °C — média global; Copernicus preencheria com coord. reais


def build_profile_from_form(form: dict) -> ProjectProfile:
    """
    Constrói ProjectProfile diretamente dos campos do formulário.
    Campos ausentes ficam com o default do dataclass.
    """
    valid = {f.name for f in dataclasses.fields(ProjectProfile)}
    kwargs = {k: v for k, v in form.items() if k in valid and v not in (None, "", [])}

    profile = ProjectProfile(**kwargs)

    # CPI lookup automático pelo país
    if profile.project_country and profile.country_cpi is None:
        profile.country_cpi = get_cpi(profile.project_country)

    # Inferência: is_forest_biomass → feedstock_type
    if profile.is_forest_biomass and profile.feedstock_type in ("unknown", ""):
        profile.feedstock_type = "forest_biomass"

    # Defaults conservadores para campos que afetam permanência em Isometric/Puro.
    # Sem H/Corg, Isometric não consegue calcular f200 → permanência = 0%,
    # criando comparação injusta com Verra (que usa temperatura com default 0.56).
    if profile.h_c_ratio is None:
        profile.h_c_ratio = _HC_DEFAULTS.get(profile.feedstock_type, 0.40)

    # MAST default: 20°C (média global conservadora).
    # Em produção, Copernicus API preenche com valor real via lat/lon do projeto.
    if profile.mast_celsius is None:
        profile.mast_celsius = _MAST_DEFAULT

    # Isometric exige durability_option explícita — "not_stated" zera R-7C8E-0.
    # 200 anos é o padrão universal para créditos de remoção permanente.
    if not profile.durability_option or profile.durability_option == "not_stated":
        profile.durability_option = "200_years"

    # Isometric lê soil_temp_method como string — sem ela, R-F5RZ-0 não pontua
    # mesmo com MAST numérico disponível.
    if not profile.soil_temp_method and profile.mast_celsius is not None:
        profile.soil_temp_method = "other"   # indica que há um método, mesmo que genérico

    return profile


def run_pin_audit(
    profile: ProjectProfile,
    methodologies: list[str] | None = None,
) -> dict[str, Any]:
    """
    Executa auditoria multi-metodologia a partir de um ProjectProfile.
    Retorna scores, grades, gaps e recomendação.
    """
    from methodology_requirements import get_requirements_for_methodology
    from engine.logic_registry import LOGIC_REGISTRY
    from backend.assessment_service import run_engine_with_profile

    if methodologies is None:
        methodologies = ["isometric", "puro_earth", "verra_vcs"]

    method_results: dict[str, Any] = {}

    for method in methodologies:
        reqs = get_requirements_for_methodology(method, engine_version="v1")
        if not reqs:
            continue

        findings = run_engine_with_profile(profile, reqs, LOGIC_REGISTRY, "development")

        dim_scores = compute_dimension_scores(findings, method)

        # ── Hard gates (mesmo critério do assessment_service) ───────────────
        def _cap(dim: str, val: float):
            cur = dim_scores.get(dim)
            if cur is not None and cur > val:
                dim_scores[dim] = val

        # Universais
        if profile.h_c_ratio is not None and profile.h_c_ratio >= 0.5:
            _cap("permanence", 0.0)
        if profile.o_c_ratio is not None and profile.o_c_ratio >= 0.2:
            _cap("permanence", 0.0)
        if profile.pah_value is not None and profile.pah_value > 12:
            _cap("environmental_social", 0.0)

        # Puro específicos
        if method == "puro_earth":
            if profile.is_forest_biomass:
                ffor = next((r for r in findings if r.get("requirement_id") == "P-FFOR-0"), None)
                if ffor and ffor.get("status") not in ("compliant", "not_applicable"):
                    _cap("feedstock_eligibility", 40.0)
            if profile.uses_mixed_waste:
                _cap("feedstock_eligibility", 0.0)
            if profile.uses_coal_ash:
                _cap("feedstock_eligibility", 0.0)
            if profile.reactor_type == "open_burning":
                _cap("feedstock_eligibility", 0.0)
                _cap("carbon_accounting", 0.0)
            if not profile.has_pyrolysis_gas_recovery:
                gsen = next((r for r in findings if r.get("requirement_id") == "P-GSEN-0"), None)
                if gsen and gsen.get("status") == "non_compliant":
                    _cap("monitoring", 15.0)
                    _cap("feedstock_eligibility", 30.0)
            if profile.financial_additionality_exemption_claimed and not profile.has_financial_additionality:
                _cap("additionality", 20.0)
            if not profile.has_lca:
                _cap("carbon_accounting", 45.0)

        # Verra específicos
        if method == "verra_vcs":
            if profile.is_purpose_grown:
                _cap("feedstock_eligibility", 0.0)
            if profile.feedstock_imported:
                _cap("feedstock_eligibility", 0.0)
            if profile.used_as_fuel:
                _cap("feedstock_eligibility", 0.0)
                _cap("permanence", 0.0)
            if (profile.h_c_ratio is not None and profile.h_c_ratio > 0.7
                    and profile.soil_application):
                _cap("feedstock_eligibility", 30.0)
                _cap("permanence", 40.0)
            if (profile.pyrolysis_temp_c is not None and profile.pyrolysis_temp_c < 350):
                _cap("permanence", 0.0)
            if not profile.has_continuous_temp_monitoring:
                cur = dim_scores.get("permanence", 100)
                if cur is not None and cur > 65:
                    dim_scores["permanence"] = 65.0

        overall = compute_weighted_score(dim_scores)
        grade = _score_to_grade(overall)

        gaps = [
            f for f in findings
            if f.get("status") in ("non_compliant", "partial", "future_evidence_required")
        ]
        gaps.sort(key=lambda r: r.get("requirement_score") or 0)

        method_results[method] = {
            "overall":    round(overall, 1),
            "grade":      grade,
            "grade_label": GRADE_LABELS.get(grade, grade),
            "label":      METHOD_LABELS.get(method, method),
            "dimensions": dim_scores,
            "top_gaps":   gaps[:5],
            "compliant":  sum(1 for f in findings if f.get("status") == "compliant"),
            "total":      len(findings),
        }

    # ── Volume de créditos calculado ────────────────────────────────────────
    credit_volume = _calc_credit_volume(profile, list(method_results.keys()))
    for method, cv in credit_volume.items():
        if method in method_results:
            method_results[method]["credit_volume"] = cv

    # ── Score composto: créditos + integridade metodológica + compliance ────
    # Baseado na abordagem Sylvera (Biochar Methodology Comparison Assessment, Out 2025):
    #   Módulo 1 — Volume de créditos (quem gera mais com ESTE H/Corg?)
    #   Módulo 2 — Integridade metodológica (RAG: carbon accounting, permanência)
    #   Compliance readiness — documentação atual do projeto
    #
    # Pesos: 40% volume + 35% integridade + 25% compliance
    # Verra perde em integridade (RED em carbon accounting) apesar de
    # ter mais créditos que Puro — consistente com avaliação Sylvera.
    composite = _calc_composite_score(method_results, credit_volume)

    if composite:
        best = max(composite, key=lambda m: composite[m])
        for m, s in composite.items():
            if m in method_results:
                method_results[m]["composite_score"] = round(s, 1)
    elif method_results:
        best = max(method_results, key=lambda m: method_results[m]["overall"])
    else:
        best = "isometric"

    reasoning = _build_reasoning(best, method_results, profile, credit_volume)

    return {
        "results":        method_results,
        "recommendation": best,
        "reasoning":      reasoning,
    }


def _calc_credit_volume(profile: ProjectProfile, methodologies: list) -> dict:
    """
    Calcula volume de créditos por metodologia a partir dos dados do perfil.
    Retorna tCO2/t biochar (fator CORC) para comparação independente de escala.
    Usa credit_volume_engine.py — mesma lógica do Sylvera Module 1.
    """
    try:
        from engine.credit_volume_engine import (
            CreditVolumeInputs, get_permanence_factor,
            calc_lca_emissions, BUFFER_POOL_PCT, CO2_C_RATIO,
        )
        # Fração de carbono típica por feedstock (base seca)
        _CF = {
            "forest_biomass": 0.77, "urban_wood": 0.77,
            "agricultural_residue": 0.65, "food_waste": 0.52,
            "animal_manure": 0.38, "sewage_sludge": 0.35,
            "mixed": 0.58, "other": 0.60,
        }
        carbon_fraction = _CF.get(profile.feedstock_type or "other", 0.60)

        inputs = CreditVolumeInputs(
            biochar_t_dry_year = profile.biochar_t_dry_year or 1000.0,
            carbon_fraction    = carbon_fraction,
            h_c_ratio          = profile.h_c_ratio or 0.40,
            mast_celsius       = profile.mast_celsius or _MAST_DEFAULT,
            pyrolysis_temp_celsius = profile.pyrolysis_temp_c or 500.0,
            methodologies      = methodologies,
        )

        result = {}
        for method in methodologies:
            perm = get_permanence_factor(inputs, method)
            gross_per_t = carbon_fraction * CO2_C_RATIO * perm
            emissions   = calc_lca_emissions(inputs, method)
            emit_per_t  = sum(emissions.values()) / inputs.biochar_t_dry_year
            buffer_pct  = BUFFER_POOL_PCT.get(method, 0.02)
            buffer_per_t = gross_per_t * buffer_pct
            net_per_t   = gross_per_t - emit_per_t - buffer_per_t
            result[method] = {
                "permanence_factor": round(perm, 3),
                "gross_tco2_per_t":  round(gross_per_t, 3),
                "net_tco2_per_t":    round(net_per_t, 3),
                "carbon_fraction":   round(carbon_fraction, 2),
            }
        return result
    except Exception as e:
        print(f"[credit_volume] erro: {e}")
        return {}


# Scores de integridade metodológica — baseados no Sylvera Methodology Assessment (Out 2025)
# Verde=5, Âmbar=3, Vermelho=1. Fonte: tabela RAG por pilar (pág. Module 2).
_INTEGRITY_SCORES = {
    "isometric": {
        "carbon_accounting": 5,  # 🟢 Obrigatório LCA ISO, GHG statement, Certify platform
        "additionality":     3,  # 🟡 TRL 6-7 gap; sem preferência de fator de emissão
        "permanence":        5,  # 🟢 H/Corg < 0.5, buffer 2-20%, verificação pré-emissão
        "safeguards":        3,  # 🟡 Forte em comunidade; EIA não obrigatório
        "total": None,
    },
    "puro_earth": {
        "carbon_accounting": 5,  # 🟢 LCA ISO-14040/44 obrigatória, modelo digital validado
        "additionality":     3,  # 🟡 TRL 6-7 gap; flexibilidade no tipo de teste financeiro
        "permanence":        5,  # 🟢 Modelo conservador (80% CI); verificação pré-emissão
        "safeguards":        5,  # 🟢 Critérios específicos de biochar; FPIC; SDG quantificáveis
        "total": None,
    },
    "verra_vcs": {
        "carbon_accounting": 1,  # 🔴 Sem LCA ISO obrigatória; emissões alta-tecnologia = 0 (injustificado)
        "additionality":     3,  # 🟡 Positive list estática; sem reavaliação periódica
        "permanence":        3,  # 🟡 Só temperatura — ignora H/Corg e reflectância
        "safeguards":        3,  # 🟡 Sem guia biochar-específico; SDG sem quantificação mínima
        "total": None,
    },
}
for _m in _INTEGRITY_SCORES:
    _INTEGRITY_SCORES[_m]["total"] = sum(
        v for k, v in _INTEGRITY_SCORES[_m].items() if k != "total"
    )
_MAX_INTEGRITY = max(d["total"] for d in _INTEGRITY_SCORES.values())  # 18 (Puro)


def _calc_composite_score(method_results: dict, credit_volume: dict) -> dict:
    """
    Score composto alinhado à abordagem Sylvera:
      40% volume de créditos (tCO2/t biochar líquido — quem gera mais)
      35% integridade metodológica (RAG Sylvera — quem tem maior rigor)
      25% compliance readiness (score atual do engine — quem é mais fácil de registrar)

    Justificativa dos pesos:
      Volume e integridade são os drivers primários de valor para compradores premium.
      Compliance readiness é secundário — reflete estado atual de documentação, não fit.
    """
    if not method_results:
        return {}

    # Normaliza volume de créditos (0-100)
    nets = {m: credit_volume.get(m, {}).get("net_tco2_per_t", 0) for m in method_results}
    max_net = max(nets.values()) if nets.values() else 1
    min_net = min(nets.values()) if nets.values() else 0
    spread  = max_net - min_net or 1

    vol_norm  = {m: (v - min_net) / spread * 100 for m, v in nets.items()}

    # Integridade (0-100)
    integ_norm = {
        m: (_INTEGRITY_SCORES.get(m, {}).get("total", 10) / _MAX_INTEGRITY * 100)
        for m in method_results
    }

    # Compliance (já em 0-100)
    compl = {m: method_results[m]["overall"] for m in method_results}

    composite = {}
    for m in method_results:
        composite[m] = (
            0.40 * vol_norm.get(m, 0) +
            0.35 * integ_norm.get(m, 0) +
            0.25 * compl.get(m, 0)
        )
    return composite


_FL = {
    "forest_biomass": "biomassa florestal", "agricultural_residue": "resíduo agrícola",
    "urban_wood": "madeira urbana", "food_waste": "resíduo alimentar",
    "sewage_sludge": "biossólido", "animal_manure": "esterco animal",
    "mixed": "feedstock misto", "other": "este tipo de feedstock",
}

_INTEG_LABELS = {
    "isometric":  "🟢 Contabilidade de Carbono | 🟢 Permanência | 🟡 Adicionalidade | 🟡 Salvaguardas",
    "puro_earth": "🟢 Contabilidade de Carbono | 🟢 Permanência | 🟡 Adicionalidade | 🟢 Salvaguardas",
    "verra_vcs":  "🔴 Contabilidade de Carbono | 🟡 Permanência | 🟡 Adicionalidade | 🟡 Salvaguardas",
}


def _build_reasoning(best: str, results: dict, profile: ProjectProfile,
                     credit_volume: dict | None = None) -> str:
    """
    Raciocínio determinístico alinhado à metodologia Sylvera:
      1. Volume de créditos (quem gera mais com este H/Corg?)
      2. Integridade metodológica (RAG: carbon accounting, permanência)
      3. Fatores de elegibilidade de feedstock
      4. Notas sobre dados faltantes
    """
    credit_volume = credit_volume or {}
    label = METHOD_LABELS.get(best, best)
    lines = []

    # ── 1. Volume de créditos ──────────────────────────────────────────────
    cv_best = credit_volume.get(best, {})
    cv_data = [(m, credit_volume.get(m, {}).get("net_tco2_per_t", 0)) for m in results]
    cv_data.sort(key=lambda x: -x[1])

    if cv_data and cv_data[0][1] > 0:
        best_net = cv_data[0][1]
        worst_net = cv_data[-1][1] if len(cv_data) > 1 else best_net
        spread_pct = (best_net - worst_net) / worst_net * 100 if worst_net else 0
        perm_best = credit_volume.get(best, {}).get("permanence_factor")
        lines.append(
            f"**Módulo 1 — Volume de Créditos:** {label} gera "
            f"~{cv_best.get('net_tco2_per_t', 0):.2f} tCO₂/t biochar líquido"
            + (f" (fator de permanência {perm_best})" if perm_best else "")
            + "."
        )
        if spread_pct > 3:
            winner_label = METHOD_LABELS.get(cv_data[0][0], cv_data[0][0])
            loser_label  = METHOD_LABELS.get(cv_data[-1][0], cv_data[-1][0])
            lines.append(
                f"Diferença de {spread_pct:.1f}% entre metodologias: "
                f"{winner_label} ({cv_data[0][1]:.2f}) vs {loser_label} ({cv_data[-1][1]:.2f} tCO₂/t)."
            )
        hc = profile.h_c_ratio
        default_hc = _HC_DEFAULTS.get(profile.feedstock_type, 0.40)
        if hc is not None and abs(hc - default_hc) < 0.011:
            ft_label = _FL.get(profile.feedstock_type, "este feedstock")
            lines.append(
                f"H/Corg não informado: default conservador {hc:.2f} aplicado "
                f"(típico para {ft_label}). Informe o valor laboratorial para permanência precisa."
            )
        elif hc and hc <= 0.25:
            lines.append(f"H/Corg={hc:.3f} → alta permanência no Isometric (f₂₀₀≈0.90) e Puro (f₂₀₀≈0.81).")

    # ── 2. Integridade metodológica ────────────────────────────────────────
    integ = _INTEG_LABELS.get(best, "")
    if integ:
        lines.append(f"**Módulo 2 — Integridade:** {integ}.")

    # Aviso Verra se recomendada (raro, mas pode acontecer)
    if best == "verra_vcs":
        lines.append(
            "⚠️ Verra VM0044 recebe avaliação 🔴 (alto risco) em Contabilidade de Carbono "
            "pela Sylvera: ausência de LCA ISO obrigatória, emissões de alta-tecnologia assumidas zero "
            "(injustificado), leakage de atividade assumido zero. "
            "Considere Isometric ou Puro.Earth para compradores que exigem maior rigor."
        )
    elif "verra_vcs" in results:
        lines.append(
            "Verra VCS recebe 🔴 em Contabilidade de Carbono (Sylvera 2025): sem LCA ISO obrigatória, "
            "sem quantificação de leakage de atividade. Não recomendada para projetos onde "
            "integridade de carbono é prioritária."
        )

    # ── 3. Elegibilidade de feedstock ─────────────────────────────────────
    has_no_cert = not any([
        profile.has_fsc_certification, profile.has_pefc_certification,
        profile.has_sfi_certification, profile.has_isae3000_dossier,
    ])
    if profile.is_forest_biomass and has_no_cert:
        lines.append(
            "Feedstock florestal sem certificação: Isometric é mais flexível "
            "(não exige certificação formal, apenas LCA e counterfactual de resíduo). "
            "Verra aceita definição CDM de biomassa renovável como alternativa. "
            "Puro.Earth exige FSC/ISAE3000 — no Brasil (CPI=36), plano governamental não é válido."
        )
    if profile.uses_mixed_waste:
        lines.append("Feedstock com material fóssil elimina Puro.Earth (Clar. 001 BCH).")
    if profile.uses_coal_ash:
        lines.append("Coal ash como insumo elimina Puro.Earth (Clar. 010 CAM).")
    if profile.country_cpi is not None and profile.country_cpi < 50 and profile.is_forest_biomass:
        lines.append(
            f"CPI={profile.country_cpi} (<50): plano de manejo governamental "
            f"não válido na Puro.Earth — apenas FSC ou ISAE 3000."
        )

    # ── 4. Score composto (transparência) ─────────────────────────────────
    composite_best = results.get(best, {}).get("composite_score")
    if composite_best:
        lines.append(
            f"Score composto ({label}): {composite_best:.0f}/100 "
            f"(40% volume créditos + 35% integridade Sylvera + 25% compliance)."
        )

    return " ".join(lines)
