from typing import Any, Dict, List, Optional

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import find_missing_paths, merge_normalized_fields
from engine.mappers.eligibility_mapper import run_eligibility_mapper
from engine.mappers.additionality_mapper import run_additionality_mapper
from engine.mappers.durability_mapper import run_durability_mapper
from engine.mappers.production_mapper import run_production_mapper
from engine.mappers.sampling_mapper import run_sampling_mapper
from engine.mappers.feedstock_mapper import run_feedstock_mapper
from engine.mappers.storage_mapper import run_storage_mapper
from engine.mappers.quantification_mapper import run_quantification_mapper
from engine.mappers.traceability_mapper import run_traceability_mapper
from engine.mappers.fallback_mapper import run_fallback_mapper
from engine.mappers.emissions_mapper import run_emissions_mapper


REQUIREMENT_HINTS = {
    # -------------------------
    # ELIGIBILITY
    # -------------------------
    "eligibility.net_negative_claim": [
        "net negative",
        "negative carbon footprint",
        "project removals",
        "removals exceed emissions",
        "3.72 t/t",
        "tco2e/t",
        "kgco2eq",
        "lca",
        "environmental additionality",
    ],
    "methodology.standard": [
        "isometric",
        "isometric standard",
        "protocol",
        "isometric protocol",
    ],
    "methodology.pathway": [
        "biochar",
        "biochar carbon removal",
        "biochar pathway",
    ],
    "methodology.production_subpathway": [
        "continuous pyrolysis",
        "continuous reactor",
        "continuous operation",
        "batch mode",
        "batch capacity",
        "rectangular kilns",
        "bst-30",
    ],

    # -------------------------
    # ADDITIONALITY
    # -------------------------
    "eligibility.additionality_claim": [
        "financial additionality",
        "regulatory additionality",
        "environmental additionality",
        "common practice",
        "baseline",
        "counterfactual",
        "irr",
        "carbon credit revenues",
        "economic barriers",
        "pricing scenarios",
    ],

    # -------------------------
    # DURABILITY
    # -------------------------
    "eligibility.durability_years": [
        "200-year durability",
        "+200-year durability",
        "1000-year durability",
        "+1000-year durability",
        "durability classification",
        "durability pathway",
        "durability threshold",
    ],
    "methodology.durability_option": [
        "200-year durability",
        "+200-year durability",
        "1000-year durability",
        "+1000-year durability",
        "combined 200 1000",
        "200/1000",
        "durability option",
        "durability classification",
        "durability pathway",
    ],

    # -------------------------
    # PRODUCTION
    # -------------------------
    "production.pyrolysis_technology": [
        "bst-30",
        "pyrolysis reactor",
        "continuous rotary",
        "continuous carbonization reactor",
        "rectangular kilns",
        "gas burners",
        "thermal control",
    ],
    "production.reactor_design_diagram": [
        "engineering design package",
        "pfd",
        "p&id",
        "process flow diagram",
        "piping and instrumentation diagrams",
        "layout drawings",
        "reactor drawing",
        "technical annex",
    ],
    "production.engineering_design_diagram": [
        "engineering design package",
        "pfd",
        "p&id",
        "process flow diagram",
        "layout drawings",
        "technical annex",
    ],
    "production.maintenance_plan": [
        "maintenance plan",
        "maintenance plan is structured around",
        "preventive maintenance",
        "routine maintenance",
        "inspection",
        "calibration",
        "annual emission testing",
    ],
    "production.maintenance_schedule": [
        "maintenance schedule",
        "maintenance schedule summary",
        "daily inspection",
        "weekly inspection",
        "monthly inspection",
        "annual servicing",
        "semi-annual calibration",
        "annual emission testing",
    ],
    "production.sensor_inventory": [
        "temperature sensors",
        "pressure sensors",
        "pressure monitoring points",
        "gas flow measurement",
        "thermocouples",
        "real-time digital monitoring",
    ],
    "production.sensor_locations": [
        "pressure monitoring points",
        "gas flow measurement",
        "sensor locations",
        "points of measurement",
        "located at",
    ],
    "production.reactor_components": [
        "reactor components",
        "combustion gases",
        "integrated furnace",
        "gas burners",
        "thermal control",
        "pressure sensors",
        "thermocouples",
    ],
    "production.material_selection_justification": [
        "material selection",
        "selected materials",
        "materials used",
        "reactor manufacturing",
        "equipment lifespan",
    ],
    "production.end_material_process_description": [
        "post-processing",
        "cooling",
        "screening",
        "storage in big bags",
        "soil application",
    ],

    # -------------------------
    # SAMPLING
    # -------------------------
    "sampling.batch_definition_days": [
        "24-hour production window",
        "hour production window",
        "within a maximum 24-hour production window",
        "production batch",
        "batch-level",
        "per production batch",
    ],
    "sampling.sampling_plan_defined": [
        "sampling plan",
        "sampling frequency",
        "analytical procedures",
        "per production batch",
        "at least once per production batch",
        "batch-level",
        "biochar samples are archived",
        "operational and laboratory data are collected per batch",
    ],
    "sampling.method": [
        "method a",
        "method b",
    ],

    # -------------------------
    # FEEDSTOCK
    # -------------------------
    "feedstock.biomass_type": [
        "eucalyptus residues",
        "harvest residues",
        "branches",
        "tops",
        "leaves",
        "bark",
        "whole trees may also be used",
    ],
    "feedstock.pre_project_biomass_use": [
        "controlled open-air burning",
        "open burning",
        "burned in the field",
        "natural decay",
        "residue disposal",
    ],
    "feedstock.feedstock_accounting_module_compliance": [
        "residue",
        "cut-off approach",
        "byproduct",
        "no land use change",
    ],
    "feedstock.moisture_measurement": [
        "moisture",
        "wet shredded biomass",
        "dry mass basis",
    ],

    # -------------------------
    # STORAGE
    # -------------------------
    "methodology.storage_pathway": [
        "soil application",
        "applied to soil",
        "soil",
        "storage pathway",
    ],
    "storage.storage_environment_stable": [
        "stable storage",
        "durable in soil",
        "soil application",
        "agricultural soil",
        "mixed into soil",
    ],
    "storage.soil.deployment_methods": [
        "deployment methods",
        "soil application",
        "applied back to the plantation area",
        "applied in eucalyptus fields",
        "application is supervised",
    ],
    "storage.stockpiling_documented": [
        "stockpiling",
        "storage in big bags",
        "stored in big bags",
    ],

    # -------------------------
    # QUANTIFICATION
    # -------------------------
    "ghg_accounting.system_boundary_defined": [
        "system boundary",
        "project boundary",
        "boundaries",
        "figure 2",
        "sources, sinks and reservoirs",
    ],
    "ghg_accounting.baseline_defined": [
        "baseline",
        "counterfactual",
        "open burning of residues",
        "absence of the project",
    ],
    "monitoring_reporting.uncertainty_method": [
        "uncertainty",
        "monte carlo",
        "variance propagation",
        "conservative parameter selection",
    ],
    "biochar.characterization.chemical_analysis_performed": [
        "laboratory analysis",
        "chemical analysis",
        "biochar is regularly analyzed",
    ],
    "biochar.characterization.lab_reports": [
        "lab report",
        "laboratory analysis",
        "accredited laboratories",
        "iso/iec 17025",
    ],
    "biochar.characterization.required_measurements_complete": [
        "batch-level elemental laboratory analysis",
        "c, h, o",
        "required measurements",
        "measurement values",
    ],
    "biochar.characterization.measurement_values": [
        "measurement values",
        "organic carbon content",
        "h/corg",
        "o/c",
        "carbon content",
    ],
    "product.standard_compliance": [
        "astm",
        "epa 8270d",
        "en 16181",
        "product standard",
        "standard compliance",
    ],

    # -------------------------
    # TRACEABILITY
    # -------------------------
    "traceability.chain_of_custody": [
        "chain of custody",
        "traceability",
        "prevent double counting",
    ],
    "traceability.records_archived": [
        "records are archived",
        "minimum of 20 years",
        "samples are archived",
        "secure digital systems",
        "regular backups",
    ],
    
    # -------------------------
    # EMISSIONS
    # -------------------------    
    
    "emissions.stack_monitoring_method": [
        "annual emission testing",
        "stack emissions",
        "air emissions",
        "emissions monitoring",
        "atmospheric emissions",
    ],
    "emissions.testing_frequency": [
        "annual emission testing",
        "annual",
        "periodic testing",
        "regular testing",
    ],
    "emissions.pyrolysis_gas_end_use_approach": [
        "combustion gases burned in an integrated furnace",
        "controlled combustion of pyrolysis gases",
        "gas burners",
        "integrated furnace",
        "heat is partially reused to sustain the process",
    ],
    "emissions.emissions_control_system": [
        "controlled combustion",
        "integrated furnace",
        "gas burners",
        "controlled combustion systems for process gases",
        "thermal control",
    ],
}


DOMAIN_REQUIREMENTS = {
    "eligibility": [
        "eligibility.net_negative_claim",
        "methodology.standard",
        "methodology.pathway",
        "methodology.production_subpathway",
    ],
    "additionality": [
        "eligibility.additionality_claim",
    ],
    "durability": [
        "eligibility.durability_years",
        "methodology.durability_option",
    ],
    "production": [
        "production.pyrolysis_technology",
        "production.reactor_design_diagram",
        "production.engineering_design_diagram",
        "production.maintenance_plan",
        "production.maintenance_schedule",
        "production.sensor_inventory",
        "production.sensor_locations",
        "production.reactor_components",
        "production.material_selection_justification",
        "production.end_material_process_description",
    ],
    "sampling": [
        "sampling.batch_definition_days",
        "sampling.sampling_plan_defined",
        "sampling.method",
    ],
    "feedstock": [
        "feedstock.biomass_type",
        "feedstock.pre_project_biomass_use",
        "feedstock.feedstock_accounting_module_compliance",
        "feedstock.moisture_measurement",
    ],
    "storage": [
        "methodology.storage_pathway",
        "storage.storage_environment_stable",
        "storage.soil.deployment_methods",
        "storage.stockpiling_documented",
    ],
    "quantification": [
        "ghg_accounting.system_boundary_defined",
        "ghg_accounting.baseline_defined",
        "monitoring_reporting.uncertainty_method",
        "biochar.characterization.chemical_analysis_performed",
        "biochar.characterization.lab_reports",
        "biochar.characterization.required_measurements_complete",
        "biochar.characterization.measurement_values",
        "product.standard_compliance",
    ],
    "traceability": [
        "traceability.chain_of_custody",
        "traceability.records_archived",
    ],
    "emissions": [
        "emissions.stack_monitoring_method",
        "emissions.testing_frequency",
        "emissions.pyrolysis_gas_end_use_approach",
        "emissions.emissions_control_system",
    ],
}


def _safe_text_from_hit(hit: Dict[str, Any]) -> str:
    candidate_keys = [
        "text",
        "content",
        "snippet",
        "chunk_text",
        "body",
        "passage",
    ]

    for key in candidate_keys:
        value = hit.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for parent_key in ["document", "result", "data"]:
        parent = hit.get(parent_key)
        if isinstance(parent, dict):
            for key in candidate_keys:
                value = parent.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    return ""


def _safe_query_from_hit(hit: Dict[str, Any]) -> str:
    for key in ["query", "search_query", "prompt", "topic"]:
        value = hit.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for parent_key in ["document", "result", "data"]:
        parent = hit.get(parent_key)
        if isinstance(parent, dict):
            for key in ["query", "search_query", "prompt", "topic"]:
                value = parent.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    return ""


def _score_text_for_hints(text: str, hints: List[str]) -> int:
    lowered = text.lower()
    score = 0

    for hint in hints:
        hint_lower = hint.lower()
        if hint_lower in lowered:
            score += 1

    return score


def _build_domain_context_from_hits(
    hits: List[Dict[str, Any]],
    methodology_context: str,
    domain_name: str,
    max_hits: int = 10,
) -> str:
    requirement_paths = DOMAIN_REQUIREMENTS.get(domain_name, [])

    scored = []
    for idx, hit in enumerate(hits):
        text = _safe_text_from_hit(hit)
        query = _safe_query_from_hit(hit)
        combined = f"{query}\n{text}".strip()

        if not combined:
            continue

        total_score = 0
        matched_requirements = []

        for req_path in requirement_paths:
            hints = REQUIREMENT_HINTS.get(req_path, [])
            req_score = _score_text_for_hints(combined, hints)
            if req_score > 0:
                total_score += req_score
                matched_requirements.append(req_path)

        if total_score > 0:
            scored.append((idx, total_score, matched_requirements, combined))

    scored.sort(key=lambda x: (-x[1], x[0]))
    top = scored[:max_hits]
    top.sort(key=lambda x: x[0])

    selected_blocks = []
    for _, _, matched_requirements, combined in top:
        req_label = ", ".join(matched_requirements)
        selected_blocks.append(
            f"[MATCHED REQUIREMENTS: {req_label}]\n{combined}"
        )

    if len(selected_blocks) < 3:
        fallback_blocks = []
        for hit in hits[:max_hits]:
            text = _safe_text_from_hit(hit)
            query = _safe_query_from_hit(hit)
            combined = f"{query}\n{text}".strip()
            if combined:
                fallback_blocks.append(combined)

        if fallback_blocks:
            selected_blocks.extend(
                [b for b in fallback_blocks if b not in selected_blocks]
            )

    project_block = "\n\n".join(selected_blocks).strip()
    methodology_block = (methodology_context or "").strip()

    return f"""
DOMAIN: {domain_name}

PROJECT EVIDENCE (requirement-scored hits):
{project_block}

METHODOLOGY CONTEXT:
{methodology_block}
""".strip()


def _build_domain_contexts(
    project_context: str,
    methodology_context: str,
    project_hits: List[Dict[str, Any]],
) -> Dict[str, str]:
    return {
        "eligibility": _build_domain_context_from_hits(project_hits, methodology_context, "eligibility"),
        "additionality": _build_domain_context_from_hits(project_hits, methodology_context, "additionality"),
        "durability": _build_domain_context_from_hits(project_hits, methodology_context, "durability"),
        "production": _build_domain_context_from_hits(project_hits, methodology_context, "production"),
        "sampling": _build_domain_context_from_hits(project_hits, methodology_context, "sampling"),
        "feedstock": _build_domain_context_from_hits(project_hits, methodology_context, "feedstock"),
        "storage": _build_domain_context_from_hits(project_hits, methodology_context, "storage"),
        "quantification": _build_domain_context_from_hits(project_hits, methodology_context, "quantification"),
        "traceability": _build_domain_context_from_hits(project_hits, methodology_context, "traceability"),
        "global": project_context or "",
        "emissions": _build_domain_context_from_hits(project_hits, methodology_context, "emissions"),
    }


def run_mapper_pipeline(
    ai_client,
    project_context: str,
    methodology_context: str,
    project_hits: Optional[List[Dict[str, Any]]] = None,
    methodology_hits: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    raw_bundle: Dict[str, Any] = {}
    collected: List[Dict[str, Any]] = []

    project_hits = project_hits or []
    methodology_hits = methodology_hits or []

    domain_contexts = _build_domain_contexts(
        project_context=project_context,
        methodology_context=methodology_context,
        project_hits=project_hits,
    )

    mapper_runs = [
        ("eligibility_mapper", run_eligibility_mapper, "eligibility"),
        ("additionality_mapper", run_additionality_mapper, "additionality"),
        ("durability_mapper", run_durability_mapper, "durability"),
        ("production_mapper", run_production_mapper, "production"),
        ("sampling_mapper", run_sampling_mapper, "sampling"),
        ("feedstock_mapper", run_feedstock_mapper, "feedstock"),
        ("storage_mapper", run_storage_mapper, "storage"),
        ("quantification_mapper", run_quantification_mapper, "quantification"),
        ("traceability_mapper", run_traceability_mapper, "traceability"),
        ("emissions_mapper", run_emissions_mapper, "emissions"),
    ]

    for name, fn, domain in mapper_runs:
        ctx = domain_contexts.get(domain, project_context)

        result = fn(
            ai_client=ai_client,
            project_context=ctx,
            methodology_context=methodology_context,
        )

        raw_bundle[name] = {
            "domain": domain,
            "project_context_used": ctx,
            "raw_extraction": result.get("raw_extraction", {"fields": []}),
        }

        collected.extend(result.get("normalized_fields", []))

    merged = merge_normalized_fields(collected)

    missing_paths = find_missing_paths(merged, EXTRACTION_FIELDS)

    fallback_result = run_fallback_mapper(
        ai_client=ai_client,
        project_context=project_context,
        methodology_context=methodology_context,
        missing_paths=missing_paths,
    )

    raw_bundle["fallback_mapper"] = {
        "domain": "global",
        "project_context_used": project_context,
        "raw_extraction": fallback_result.get("raw_extraction", {"fields": []}),
    }

    merged = merge_normalized_fields(
        merged + fallback_result.get("normalized_fields", [])
    )

    return {
        "normalized_fields": merged,
        "raw_extraction_bundle": raw_bundle,
    }
