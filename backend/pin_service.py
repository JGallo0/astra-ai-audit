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

    # Inferências simples
    if profile.is_forest_biomass and profile.feedstock_type == "unknown":
        profile.feedstock_type = "forest_biomass"

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

    # ── Recomendação ────────────────────────────────────────────────────────
    if method_results:
        best = max(method_results, key=lambda m: method_results[m]["overall"])
        reasoning = _build_reasoning(best, method_results, profile)
    else:
        best, reasoning = "isometric", "Sem dados suficientes para recomendação."

    return {
        "results":        method_results,
        "recommendation": best,
        "reasoning":      reasoning,
    }


def _build_reasoning(best: str, results: dict, profile: ProjectProfile) -> str:
    """Raciocínio determinístico da recomendação de metodologia."""
    label = METHOD_LABELS.get(best, best)
    score = results[best]["overall"]
    dims  = results[best].get("dimensions", {})

    lines = [f"**{label}** apresenta a maior aderência ao perfil do projeto ({score:.0f}%)."]

    # Feedstock
    if profile.is_forest_biomass and not any([
        profile.has_fsc_certification, profile.has_pefc_certification,
        profile.has_sfi_certification, profile.has_isae3000_dossier,
    ]):
        lines.append(
            "Biomassa florestal sem certificação favorece Isometric (critérios mais flexíveis) "
            "em relação à Puro.Earth (exige FSC/ISAE3000)."
        )

    if profile.uses_mixed_waste:
        lines.append("Feedstock misto torna Puro.Earth inelegível — eliminatório absoluto (Clarificação 001).")

    if profile.uses_coal_ash:
        lines.append("Coal ash torna Puro.Earth inelegível — eliminatório absoluto (Clarificação 010).")

    # Permanência Verra vs H/Corg
    if profile.pyrolysis_temp_c is not None and profile.pyrolysis_temp_c > 600:
        prd = 0.89
        lines.append(
            f"Temperatura de pirólise {profile.pyrolysis_temp_c:.0f}°C → PRde={prd} na Verra "
            f"(equivalente a f₂₀₀ alto na Isometric/Puro)."
        )
    elif profile.h_c_ratio is not None and profile.h_c_ratio < 0.3:
        lines.append(
            f"H/Corg={profile.h_c_ratio:.2f} favorece permanência alta na Isometric e Puro.Earth "
            f"(modelo Woolf 2021)."
        )

    # CPI e caminho florestal Puro
    if profile.is_forest_biomass and profile.country_cpi is not None and profile.country_cpi < 50:
        lines.append(
            f"CPI do país = {profile.country_cpi} (< 50): plano de manejo governamental não disponível "
            f"na Puro.Earth — apenas FSC ou ISAE 3000 são caminhos válidos."
        )

    # Verra feedstock elegível
    if profile.is_purpose_grown:
        lines.append("Feedstock purpose-grown exclui o projeto da Verra VCS (AC 4a) e da Puro.Earth.")

    # Sem LCA
    if not profile.has_lca:
        lines.append(
            "Sem LCA iniciada: Puro.Earth é penalizada (cap 45% em carbon_accounting). "
            "Isometric e Verra aceitam LCA futura no desenvolvimento do PDD."
        )

    # Gap principal do segundo colocado
    runners = [(m, d["overall"]) for m, d in results.items() if m != best]
    runners.sort(key=lambda x: -x[1])
    if runners:
        second, second_score = runners[0]
        diff = score - second_score
        if diff < 10:
            lines.append(
                f"{METHOD_LABELS.get(second, second)} é alternativa próxima "
                f"(diferença de {diff:.0f}pp) — considere os critérios específicos antes de decidir."
            )

    return " ".join(lines)
