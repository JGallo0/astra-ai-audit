"""
Co2mply — Methodology Assessment Service

Avalia um projeto contra TODAS as metodologias disponíveis com o mesmo
framework de extração (ProjectProfile) e dimensões universais comparáveis.

Fluxo:
  1. Extrai ProjectProfile via LLM (perguntas booleanas estruturadas)
  2. Para cada metodologia: carrega requisitos + lógica → executa engine
  3. Calcula scores por dimensão universal (6 dimensões, pesos fixos)
  4. Compara, recomenda e gera reasoning determinístico
"""

from __future__ import annotations
import dataclasses
import json
from typing import Any

from engine.project_profile import (
    ProjectProfile, extract_project_profile, profile_to_legacy_dict
)
from engine.dimension_map import (
    UNIVERSAL_DIMENSIONS, DIMENSION_MAPS,
    compute_dimension_scores, compute_weighted_score,
)
from methodology_requirements import get_requirements_for_methodology


# ── Probes metodológicos ──────────────────────────────────────────────────────

METHODOLOGY_PROBES = {
    "puro_earth": {
        "has_isae3000_dossier": (
            "Does the PDD reference an ISAE 3000 third-party audited dossier "
            "for forest biomass sustainability? Answer TRUE only if explicitly mentioned."
        ),
        "govt_plan_authority":    "Does the PDD identify a local government authority overseeing forest management?",
        "govt_plan_requirements": "Does the PDD describe the local sustainability requirements in essence?",
        "govt_plan_oversight":    "Does the PDD document the type of oversight (logging notices, approvals, inspections)?",
        "govt_plan_documents":    "Does the PDD list supporting documents with English summaries?",
        "uses_coal_ash":          "Does the PDD mention coal ash or coal combustion by-products as feedstock?",
        "financial_additionality_exemption_claimed": (
            "Does the PDD claim that being 'first-of-its-kind' exempts the project "
            "from financial additionality analysis?"
        ),
        "has_puro_sdg_template":  "Does the PDD use the Puro.earth SDG reporting template?",
        "has_pyrolysis_gas_recovery": (
            "Does the PDD describe that pyrolysis gases are recovered or combusted (e.g. via gas burner, "
            "flare, or energy recovery system)? Answer FALSE if gases are vented without treatment."
        ),
    },
    "isometric": {
        "has_pyrolysis_gas_recovery": (
            "Does the PDD describe that pyrolysis gases are recovered or combusted "
            "(via gas burner, flare, or energy recovery)? FALSE if gases are vented."
        ),
        "uses_lembrechts_database": (
            "Does the PDD specifically reference the Lembrechts et al. soil temperature database "
            "for permanence calculations?"
        ),
        "has_isometric_protocol_justification": (
            "Does the PDD include a justification for eligibility specifically under the Isometric "
            "Biochar Production and Storage Protocol?"
        ),
        # Fix 2: perguntas Isometric-específicas que o profile genérico não capta bem
        "has_system_boundary": (
            "Does the PDD define the project's system boundary, including temporal scope, "
            "geographic boundary, and GHG sources included/excluded?"
        ),
        "has_baseline": (
            "Does the PDD describe a baseline scenario or counterfactual — what would happen "
            "to the feedstock or the carbon if this project did not exist?"
        ),
        "has_leakage_assessment": (
            "Does the PDD assess or mention leakage — GHG emissions outside the project boundary "
            "caused by the project activities?"
        ),
        "has_lca": (
            "Does the PDD include or reference a Life Cycle Assessment (LCA) covering feedstock, "
            "production, and storage/application stages?"
        ),
        "has_uncertainty_analysis": (
            "Does the PDD describe methods for uncertainty analysis or sensitivity analysis "
            "of the GHG quantification?"
        ),
        "has_monitoring_table": (
            "Does the PDD include a monitoring plan or table listing parameters to be monitored, "
            "with frequency and responsible parties?"
        ),
        "has_data_storage_plan": (
            "Does the PDD describe how monitoring data will be collected, stored, and retained?"
        ),
        "durability_option": (
            "Does the PDD select a durability threshold for biochar permanence? "
            "Answer '200_years', '1000_years', or '' if not stated."
        ),
        "has_soil_temp_method": (
            "Does the PDD describe a method for measuring or obtaining mean annual soil temperature "
            "at the biochar application site?"
        ),
        "has_reversal_risk_assessment": (
            "Does the PDD include a reversal risk assessment or mention a buffer pool "
            "for biochar permanence?"
        ),
        "has_stakeholder_consultation": (
            "Does the PDD document a stakeholder consultation process, including who was consulted "
            "and how their input was considered?"
        ),
        "has_grievance_mechanism": (
            "Does the PDD describe a grievance mechanism for stakeholders to raise concerns?"
        ),
        "has_engineering_diagram": (
            "Does the PDD include or reference an engineering design diagram of the pyrolysis reactor?"
        ),
        "has_gas_sensors": (
            "Does the PDD describe sensors or methods to detect or quantify pyrolysis gas leakage?"
        ),
        "has_maintenance_plan": (
            "Does the PDD include a reactor maintenance plan?"
        ),
        "has_iso17025_lab": (
            "Does the PDD identify a laboratory with ISO 17025 accreditation for biochar analysis?"
        ),
        "sampling_method": (
            "What sampling method does the PDD describe? "
            "Answer 'method_a' (every batch), 'method_b' (1 per 10 batches), or '' if not stated."
        ),
        "has_financial_additionality": (
            "Does the PDD demonstrate financial additionality — that the project would not be "
            "economically viable without carbon revenue?"
        ),
        "has_regulatory_additionality": (
            "Does the PDD confirm the project is not required by existing laws or regulations?"
        ),
        "has_no_net_env_harm": (
            "Does the PDD demonstrate that the project causes no net environmental harm?"
        ),
        "has_pollution_prevention": (
            "Does the PDD describe measures to prevent pollution from PAHs, heavy metals, "
            "PCBs, or dioxins?"
        ),
        "has_adaptive_management": (
            "Does the PDD include an adaptive management plan with conditions for pausing "
            "or stopping the project?"
        ),
    },
}


def _make_ai_client(openai_client: Any, model: str):
    """Cria um ai_client compatível com extract_project_data_from_contexts()."""
    def ai_client(prompt: str) -> str:
        resp = openai_client.responses.create(
            model=model,
            input=prompt,
            temperature=0,
        )
        return getattr(resp, "output_text", "") or ""
    return ai_client


def _extract_isometric_project_data(
    pdd_text: str,
    openai_client: Any,
    model: str,
) -> dict:
    """
    Roda a extração Isometric completa (mapper + inference + build) a partir
    do texto do PDD. Equivalente ao que o AuditEngine faz na auditoria regular.
    Retorna project_data dict pronto para run_engine().
    """
    try:
        from engine.document_mapper import extract_project_data_from_contexts
        from engine.requirement_logic import apply_inference_rules

        ai_client = _make_ai_client(openai_client, model)

        mapped = extract_project_data_from_contexts(
            ai_client=ai_client,
            project_context=pdd_text,
            methodology_context="",   # metodologia sem hits específicos
            project_hits=[],
            methodology_hits=[],
        )
        project_data = mapped.get("project_data", {}) if isinstance(mapped, dict) else {}
        # Aplica regras de inferência Isometric
        project_data = apply_inference_rules(project_data, methodology_key="isometric")
        project_data.setdefault("methodology", {})["standard"] = "Isometric"
        return project_data
    except Exception as e:
        print(f"[assessment] Isometric extraction error: {e}")
        return {}


async def run_probes(
    profile: ProjectProfile,
    methodology_key: str,
    pdd_text: str,
    openai_client: Any,
    model: str,
) -> ProjectProfile:
    """Executa perguntas específicas da metodologia e atualiza o profile."""
    probes = METHODOLOGY_PROBES.get(methodology_key, {})
    if not probes:
        return profile

    questions = "\n".join(f'"{k}": {q}' for k, q in probes.items())
    prompt = f"""Answer these specific questions about the project PDD.
Return only valid JSON. TRUE only if explicitly stated. When in doubt: FALSE.

PDD CONTENT (excerpt):
{pdd_text[:8000]}

QUESTIONS:
{{{questions}}}

Format: {{"field_name": {{"value": bool, "evidence": "quote or empty"}}}}"""

    resp = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Carbon project auditor. Only JSON responses."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = json.loads(resp.choices[0].message.content)
    valid_fields = {f.name for f in dataclasses.fields(ProjectProfile)}
    for field_name, entry in raw.items():
        if field_name in valid_fields:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val is not None:
                try:
                    setattr(profile, field_name, val)
                except Exception:
                    pass
    return profile


def run_engine_with_profile(
    profile: ProjectProfile,
    requirements: list,
    logic_registry: dict,
    audit_mode: str = "development",
) -> list:
    """
    Roda o engine com ProjectProfile.
    Funções que aceitam ProjectProfile: chamadas diretamente.
    Funções legadas (aceitam dict): chamadas via adapter.
    """
    legacy_dict = profile_to_legacy_dict(profile)
    results = []

    for req in requirements:
        req_id   = req.get("id") or req.get("requirement_id", "")
        logic_fn = req.get("logic")
        title    = req.get("title") or req.get("requirement_name", "")
        module   = req.get("module", "")

        # Check mode_applicability
        mode_app = req.get("mode_applicability", "both")
        if mode_app == "operational_only" and audit_mode == "development":
            result = {
                "status": "not_applicable",
                "requirement_score": None,
                "notes": ["Evidência aplicável em Modo Operacional."],
                "gap": "",
                "recommendation": "",
            }
        else:
            fn = logic_registry.get(logic_fn) if logic_fn else None
            if fn:
                try:
                    # Try with profile first (new functions)
                    import inspect
                    sig = inspect.signature(fn)
                    first_param = list(sig.parameters.values())[0]
                    # If first param annotation is ProjectProfile, pass directly
                    ann = first_param.annotation
                    if ann is ProjectProfile or str(ann) == 'ProjectProfile':
                        result = fn(profile, audit_mode)
                    else:
                        result = fn(legacy_dict, audit_mode)
                except Exception:
                    # Fallback: try legacy dict
                    try:
                        result = fn(legacy_dict, audit_mode)
                    except Exception as e:
                        result = {
                            "status": "error",
                            "requirement_score": 0,
                            "notes": [f"Erro: {e}"],
                            "gap": "",
                            "recommendation": "",
                        }
            else:
                result = {
                    "status": "partial",
                    "requirement_score": 50,
                    "notes": ["Função de lógica não mapeada."],
                    "gap": "Lógica específica não implementada.",
                    "recommendation": "",
                }

        results.append({
            "requirement_id": req_id,
            "title":          title,
            "module":         module,
            "source_url":     req.get("source_url", ""),
            "requirement_text": req.get("requirement_text", ""),
            **result,
        })

    return results


async def run_methodology_assessment(
    project_id: str,
    pdd_text: str,
    methodologies: list[str],
    openai_client: Any,
    model: str,
    audit_mode: str = "development",
    cached_project_data: dict = None,
) -> dict:
    """
    Avalia o projeto contra todas as metodologias e retorna comparação.

    Returns:
        {
          "profile": {...},
          "methodologies": {
            "isometric":  {"overall": X, "grade": "A", "dimensions": {...}, "gaps": [...], "findings": [...]},
            "puro_earth": {...},
          },
          "recommendation": "isometric",
          "recommendation_reasoning": "...",
          "differential": [...],
        }
    """
    from engine.logic_registry import LOGIC_REGISTRY

    # 1. Extrai profile universal (1 chamada LLM)
    profile = await extract_project_profile(pdd_text, openai_client, model)

    # 2. Probes por metodologia (1 chamada por metodologia)
    for method in methodologies:
        profile = await run_probes(profile, method, pdd_text, openai_client, model)

    # Resolve country_cpi com CPI real (substitui qualquer valor heurístico)
    if profile.project_country:
        try:
            from engine.country_cpi import get_cpi
            real_cpi = get_cpi(profile.project_country)
            if real_cpi is not None:
                profile.country_cpi = float(real_cpi)
        except Exception:
            pass
    # Se país não identificado mas localização tem nome de país, tenta inferir
    if profile.country_cpi is None and profile.project_locations:
        try:
            from engine.country_cpi import get_cpi
            for loc in profile.project_locations:
                cpi = get_cpi(str(loc))
                if cpi is not None:
                    profile.country_cpi = float(cpi)
                    break
        except Exception:
            pass

    # 3. Executa engine para cada metodologia
    method_results = {}
    for method in methodologies:
        reqs = get_requirements_for_methodology(method, engine_version="v1")
        if not reqs:
            continue

        # Isometric: usa extração nativa (project_data do banco ou extração fresca).
        # Garante que as funções Isometric recebam dados equivalentes à auditoria
        # regular — sem dependência de validação prévia.
        # Outros (Puro, etc.): usa ProjectProfile (extração booleana).
        if method == "isometric":
            isometric_pd = None

            # Prioridade 1: project_data cacheado do banco (mais rápido)
            if cached_project_data:
                isometric_pd = cached_project_data

            # Prioridade 2: extrair fresh a partir do PDD text
            if not isometric_pd and pdd_text and len(pdd_text) > 100:
                print(f"[assessment] Isometric: sem cache — extraindo project_data fresh...")
                isometric_pd = _extract_isometric_project_data(pdd_text, openai_client, model)

            if isometric_pd:
                try:
                    from engine.requirement_logic import run_engine, apply_inference_rules
                    pd = dict(isometric_pd)
                    pd.setdefault("methodology", {})["standard"] = "Isometric"
                    pd = apply_inference_rules(pd, methodology_key="isometric")
                    engine_out = run_engine(
                        pd, reqs, audit_mode=audit_mode,
                        profile=None, methodology_key="isometric",
                    )
                    findings = engine_out.get("results", engine_out) if isinstance(engine_out, dict) else engine_out
                except Exception as e:
                    print(f"[assessment] Isometric engine error: {e}")
                    findings = run_engine_with_profile(profile, reqs, LOGIC_REGISTRY, audit_mode)
            else:
                # Fallback final: profile (piora qualidade mas não trava)
                findings = run_engine_with_profile(profile, reqs, LOGIC_REGISTRY, audit_mode)
        else:
            findings = run_engine_with_profile(profile, reqs, LOGIC_REGISTRY, audit_mode)
        dim_scores = compute_dimension_scores(findings, method)

        # ══════════════════════════════════════════════════════════════════════
        # HARD GATES — Critérios eliminatórios por metodologia
        # Cada cap reflete o impacto real do gap na capacidade de certificação.
        # ══════════════════════════════════════════════════════════════════════

        def _cap(dim: str, max_val: float):
            """Aplica cap em uma dimensão se o score atual for maior."""
            cur = dim_scores.get(dim)
            if cur is not None and cur > max_val:
                dim_scores[dim] = max_val

        # ── Critérios comuns a ambas as metodologias ──────────────────────────

        # H/Corg ≥ 0,5 → permanência = 0% (projeto não pode ser certificado)
        if profile.h_c_ratio is not None and profile.h_c_ratio >= 0.5:
            _cap("permanence", 0.0)

        # O/Corg ≥ 0,2 → permanência = 0% (eliminatório ambas)
        if profile.o_c_ratio is not None and profile.o_c_ratio >= 0.2:
            _cap("permanence", 0.0)

        # PAH acima do limite WBC (~12 mg/kg) → ambiental = 0%
        if profile.pah_value is not None and profile.pah_value > 12:
            _cap("environmental_social", 0.0)

        # PCB acima do limite (0,2 mg/kg) → ambiental = 0%
        if profile.pcb_value is not None and profile.pcb_value > 0.2:
            _cap("environmental_social", 0.0)

        # PCDD/F acima do limite (20 ng/kg) → ambiental = 0%
        if profile.pcdd_f_value is not None and profile.pcdd_f_value > 20:
            _cap("environmental_social", 0.0)

        # Gases de pirólise NÃO recuperados → monitoramento e feedstock penalizados
        # (impacta net-negativity, que é hard gate em ambas metodologias)
        if profile.has_gas_sensors is False and method in ("puro_earth", "isometric"):
            # Se explicitamente ausente (não apenas desconhecido):
            gas_req_id = "P-GSEN-0" if method == "puro_earth" else "R-SZK5-0"
            gas_req = next((r for r in findings if r.get("requirement_id") == gas_req_id), None)
            if gas_req and gas_req.get("status") == "non_compliant":
                _cap("monitoring", 20.0)

        # ── Critérios específicos Puro.Earth ──────────────────────────────────
        if method == "puro_earth":

            # 1. Biomassa florestal sem certificação (P-FFOR-0)
            # Gap estrutural — projeto não pode ser registrado sem FSC/ISAE3000/plano gov.
            if profile.is_forest_biomass:
                ffor = next((r for r in findings if r.get("requirement_id") == "P-FFOR-0"), None)
                if ffor and ffor.get("status") not in ("compliant", "not_applicable"):
                    _cap("feedstock_eligibility", 40.0)

            # 2. Feedstock misto (fossil+biogênico) → eliminatório absoluto (Clarificação 001 BCH)
            if profile.uses_mixed_waste:
                feli = next((r for r in findings if r.get("requirement_id") == "P-FELI-0"), None)
                if feli and feli.get("status") == "non_compliant":
                    _cap("feedstock_eligibility", 0.0)

            # 3. Coal ash → eliminatório absoluto (Clarificação 010 CAM)
            if profile.uses_coal_ash:
                _cap("feedstock_eligibility", 0.0)

            # 4. Gases de pirólise não recuperados/combustados → eliminatório Puro
            # (Hard gate explícito na tabela de elegibilidade do VVB)
            if not profile.has_pyrolysis_gas_recovery:
                # Apenas penaliza se o processo foi descrito e gases ventiláveis identificados
                gsen = next((r for r in findings if r.get("requirement_id") == "P-GSEN-0"), None)
                if gsen and gsen.get("status") == "non_compliant":
                    _cap("monitoring", 15.0)
                    _cap("feedstock_eligibility", 30.0)

            # 5. Alega isenção de adicionalidade por first-of-its-kind → Puro rejeita
            # (Clarificação 005 ADD — fechado explicitamente)
            if profile.financial_additionality_exemption_claimed and not profile.has_financial_additionality:
                _cap("additionality", 20.0)

            # 6. Sem LCA alguma → Puro exige LCA explícita e prescritiva (A1→B1)
            # Isometric tolera GHG statement sem LCA formal
            if not profile.has_lca:
                _cap("carbon_accounting", 45.0)

        overall    = compute_weighted_score(dim_scores)
        grade      = _score_to_grade(overall)
        gaps       = [f for f in findings if f.get("status") in
                      ("non_compliant", "partial", "future_evidence_required")]
        gaps.sort(key=lambda r: r.get("requirement_score") or 0)

        # RAG por parâmetro (estilo Sylvera)
        try:
            from engine.rag_parameter_map import compute_rag_scores
            rag_scores = compute_rag_scores(findings, method)
        except Exception as e:
            print(f"[rag] error: {e}")
            rag_scores = {}

        method_results[method] = {
            "overall":       overall,
            "grade":         grade,
            "dimensions":    dim_scores,
            "rag":           rag_scores,
            "gaps":          gaps[:10],
            "findings":      findings,
            "req_count":     len(reqs),
            "compliant":     sum(1 for f in findings if f.get("status") == "compliant"),
            "non_compliant": sum(1 for f in findings if f.get("status") == "non_compliant"),
        }

    # 4. Credit volume estimado (integração Module 1 no assessment)
    credit_volume_summary = {}
    try:
        from engine.credit_volume_engine import CreditVolumeInputs, compare_methodologies as _cv_compare
        biochar_t = profile.feedstock_t_ano * max(profile.feedstock_yield or 0.28, 0.01) if hasattr(profile, 'feedstock_t_ano') and profile.feedstock_t_ano else 1000
        cv_inputs = CreditVolumeInputs(
            biochar_t_dry_year=biochar_t,
            h_c_ratio=profile.h_c_ratio or 0.35,
            mast_celsius=profile.country_cpi and 20.0 or 20.0,   # placeholder — Copernicus integrado
            methodologies=[m for m in methodologies if m in ("isometric", "puro_earth", "verra_vcs")],
        )
        cv_result = _cv_compare(cv_inputs)
        for m, r in cv_result.get("results", {}).items():
            credit_volume_summary[m] = {
                "net_co2_year":      r.get("net_co2_year"),
                "corc_factor":       r.get("corc_factor"),
                "permanence_factor": r.get("permanence_factor"),
            }
    except Exception as e:
        print(f"[credit_volume] error in assessment: {e}")

    # 5. Recomendação
    if not method_results:
        return {"profile": dataclasses.asdict(profile), "methodologies": {}, "recommendation": None}

    best = max(method_results, key=lambda m: method_results[m]["overall"])
    reasoning = _build_reasoning(best, method_results, profile)
    differential = _build_differential(method_results)

    return {
        "profile":        dataclasses.asdict(profile),
        "credit_volume":  credit_volume_summary,
        "methodologies":  {
            k: {**v, "findings": v["findings"]}
            for k, v in method_results.items()
        },
        "recommendation":          best,
        "recommendation_confidence": round(
            method_results[best]["overall"] - max(
                (v["overall"] for k, v in method_results.items() if k != best),
                default=0
            ), 1
        ),
        "recommendation_reasoning": reasoning,
        "differential":            differential,
    }


def _score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    return "C"


def _build_reasoning(
    best: str,
    results: dict,
    profile: ProjectProfile,
) -> str:
    """Reasoning determinístico baseado no profile e nos scores por dimensão."""
    labels = {"isometric": "Isometric Biochar v1.2", "puro_earth": "Puro.Earth Edition 2025"}
    best_label = labels.get(best, best)
    best_score = results[best]["overall"]

    reasons = []

    # Feedstock-specific reasoning — biomassa florestal sem certificação
    if profile.is_forest_biomass:
        has_cert = (profile.has_fsc_certification or profile.has_sfi_certification
                    or profile.has_pefc_certification or profile.has_isae3000_dossier)
        if not has_cert:
            puro_fd = (results.get("puro_earth", {}).get("dimensions") or {}).get("feedstock_eligibility")
            # Razão principal — independente de qual metodologia ganhou
            cpi_note = (
                f" O Brasil tem CPI {profile.country_cpi:.0f} ≥ 50, então o caminho do plano governamental "
                f"é teoricamente disponível — mas exige documentação formal dos 4 itens obrigatórios."
                if profile.country_cpi and profile.country_cpi >= 50 else
                " O país do projeto tem CPI < 50, excluindo também o caminho do plano governamental."
            )
            reasons.append(
                "⚠️ Fator decisivo: o projeto usa biomassa florestal sem certificação FSC/SFI/PEFC "
                "ou dossiê ISAE 3000. Para o Puro.Earth Edition 2025, isso é um gap estrutural — "
                "o projeto não pode ser registrado sem uma dessas comprovações."
                + cpi_note +
                " Isometric avalia sustentabilidade de biomassa de forma mais flexível, "
                "sem exigir certificação formal específica."
            )

    # SDG reasoning
    if not profile.has_sdg_reporting:
        puro_res = results.get("puro_earth", {})
        if puro_res and puro_res.get("overall", 100) < results[best].get("overall", 0):
            reasons.append(
                "Relatório de ODS (SDG) não identificado no PDD. Puro.Earth exige submission formal de SDG; "
                "Isometric não tem este requisito como entregável separado."
            )

    # Mixed waste
    if profile.uses_mixed_waste and best != "puro_earth":
        reasons.append(
            "Feedstock misto (fóssil + biogênico) é explicitamente proibido pelo Puro.Earth "
            "(Clarificação 001 BCH). Isometric avalia caso a caso."
        )

    # First-of-its-kind
    if profile.is_first_of_its_kind and profile.financial_additionality_exemption_claimed:
        reasons.append(
            "O projeto alega isenção de análise de adicionalidade por ser first-of-its-kind. "
            "Puro.Earth (Clarificação 005 ADD) rejeita esta isenção; Isometric permite mais flexibilidade."
        )

    if not reasons:
        reasons.append(
            f"{best_label} apresentou maior aderência geral ao perfil do projeto "
            f"({best_score:.0f}% de score médio ponderado)."
        )

    return " ".join(reasons)


def _build_differential(results: dict) -> list:
    """Lista de diferenças por dimensão entre as metodologias."""
    if len(results) < 2:
        return []

    methods = list(results.keys())
    if len(methods) < 2:
        return []

    a, b = methods[0], methods[1]
    diff = []

    LABELS = {"isometric": "Isometric", "puro_earth": "Puro.Earth"}
    DIM_CONTEXT = {
        "feedstock_eligibility": {
            "isometric_advantage": "Isometric avalia 'sustainable biomass' de forma mais flexível — sem certificação formal obrigatória.",
            "puro_earth_advantage": "Puro.Earth tem critérios de feedstock mais restritos, garantindo maior rigor na cadeia de custódia.",
        },
        "environmental_social": {
            "puro_earth_advantage": "Puro.Earth exige relatório de ODS formal; Isometric trata como salvaguarda opcional.",
            "isometric_advantage": "Isometric não exige relatório de ODS separado.",
        },
        "additionality": {
            "puro_earth_advantage": "Puro.Earth fecha brechas como 'first-of-its-kind' — maior rigor em adicionalidade.",
            "isometric_advantage": "Isometric tem mais flexibilidade interpretativa em adicionalidade financeira.",
        },
    }

    for dim in UNIVERSAL_DIMENSIONS:
        score_a = (results[a].get("dimensions") or {}).get(dim)
        score_b = (results[b].get("dimensions") or {}).get(dim)
        if score_a is None or score_b is None:
            continue
        delta = abs(score_a - score_b)
        if delta < 5:
            continue  # diferença irrelevante

        better = a if score_a > score_b else b
        context = DIM_CONTEXT.get(dim, {})
        reason_key = f"{better}_advantage"
        reason = context.get(reason_key, f"{LABELS.get(better, better)} tem maior aderência nesta dimensão.")

        diff.append({
            "dimension":      dim,
            "label":          UNIVERSAL_DIMENSIONS[dim]["label"],
            methods[0]:       score_a,
            methods[1]:       score_b,
            "delta":          round(delta, 1),
            "better":         better,
            "better_label":   LABELS.get(better, better),
            "reasoning":      reason,
        })

    diff.sort(key=lambda x: x["delta"], reverse=True)
    return diff
