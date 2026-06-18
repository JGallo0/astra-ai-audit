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
from engine.mappers.management_mapper import run_management_mapper
from engine.mappers.biochar_characterization_mapper import run_biochar_characterization_mapper


REQUIREMENT_HINTS = {
    # =========================================================
    # ELIGIBILITY
    # =========================================================
    "eligibility.net_negative_claim": [
        "net negative",
        "net-negative",
        "negative carbon footprint",
        "project removals",
        "removals exceed emissions",
        "removals are greater than emissions",
        "positive net removals",
        "net removals",
        "tco2e/t",
        "kgco2eq",
        "kg co2eq",
        "co2 removed",
        "co2 removal",
        "climate impact",
        "lca",
        "life cycle assessment",
        "environmental additionality",
        "baseline emissions",
        "leakage emissions",
        "project emissions",
    ],
    "methodology.standard": [
        "isometric",
        "isometric standard",
        "isometric protocol",
        "isometric bicrs",
        "bicrs",
        "under the isometric protocol",
    ],
    "methodology.pathway": [
        "biochar",
        "biochar carbon removal",
        "biochar pathway",
        "co2 removal by biochar",
        "biochar project",
    ],
    "methodology.production_subpathway": [
        "continuous pyrolysis",
        "continuous reactor",
        "continuous operation",
        "continuous rotary",
        "rotary kiln",
        "batch mode",
        "batch capacity",
        "batch operation",
        "rectangular kilns",
        "kilns operate in batch mode",
        "bst-30",
        "standard production subpathway",
    ],

    # =========================================================
    # ADDITIONALITY
    # =========================================================
    "eligibility.additionality_claim": [
        "financial additionality",
        "regulatory additionality",
        "environmental additionality",
        "common practice",
        "common-practice",
        "common practice analysis",
        "baseline",
        "counterfactual",
        "irr",
        "carbon credit revenues",
        "economic barriers",
        "pricing scenarios",
        "not common practice",
        "not widely adopted",
        "would not occur without",
        "viability depends on carbon credits",
        "additionality demonstration",
    ],

    # =========================================================
    # DURABILITY
    # =========================================================
    "eligibility.durability_years": [
        "200-year durability",
        "+200-year durability",
        "1000-year durability",
        "+1000-year durability",
        "durability classification",
        "durability pathway",
        "durability threshold",
        "durability class",
        "permanence threshold",
        "permanence category",
        "carbon permanence",
        "long-term storage",
        "long term storage",
        "biochar stability",
        "stable carbon",
        "biochar persistence",
        "remains stable",
        "stable over centuries",
        "hundreds of years",
        "at least 200 years",
        "at least 1000 years",
        "under the +200-year threshold",
        "under the 200-year threshold",
        "selected durability threshold",
        "selected permanence threshold",
    ],
    "methodology.durability_option": [
        "200-year durability",
        "+200-year durability",
        "1000-year durability",
        "+1000-year durability",
        "combined 200 1000",
        "combined_200_1000",
        "200/1000",
        "durability option",
        "durability classification",
        "durability pathway",
        "durability threshold",
        "durability class",
        "permanence threshold",
        "permanence category",
        "selected durability threshold",
        "selected permanence threshold",
        "project applies the +200-year durability classification",
        "project applies the 200-year durability classification",
    ],

    # =========================================================
    # PRODUCTION
    # =========================================================
    "production.pyrolysis_technology": [
        "bst-30",
        "pyrolysis reactor",
        "continuous rotary",
        "continuous carbonization reactor",
        "continuous rotary carbonization reactor",
        "continuous rotary pyrolysis reactor",
        "rotary kiln",
        "carbonization furnace",
        "cogeneration system",
        "gasification system",
        "thermochemical conversion",
        "biochar production system",
        "industrial biochar system",
        "retort",
        "kiln",
        "reactor",
        "gas burners",
        "thermal control",
        "integrated gas recovery",
        "sealed combustion system",
    ],
    "production.reactor_design_diagram": [
        "engineering design package",
        "pfd",
        "p&id",
        "process flow diagram",
        "process flow diagrams",
        "piping and instrumentation diagrams",
        "layout drawings",
        "reactor drawing",
        "technical annex",
        "supporting documentation",
        "engineering diagram",
        "reactor layout",
    ],
    "production.engineering_design_diagram": [
        "engineering design package",
        "pfd",
        "p&id",
        "process flow diagram",
        "process flow diagrams",
        "piping and instrumentation diagrams",
        "layout drawings",
        "reactor drawing",
        "technical annex",
        "engineering diagram",
    ],
    "production.maintenance_plan": [
        "maintenance plan",
        "maintenance plan is structured around",
        "preventive maintenance",
        "routine maintenance",
        "inspection",
        "routine visual inspection",
        "negative-pressure system verification",
        "leakage verification",
        "annual leakage verification",
        "calibration",
        "annual emission testing",
        "mechanical integrity",
        "seal inspection",
    ],
    "production.maintenance_schedule": [
        "maintenance schedule",
        "maintenance schedule summary",
        "daily inspection",
        "weekly inspection",
        "monthly inspection",
        "quarterly inspection",
        "annual servicing",
        "biannual sensor calibration",
        "semi-annual calibration",
        "annual emission testing",
        "frequency activity",
    ],
    "production.sensor_inventory": [
        "temperature sensors",
        "pressure sensors",
        "pressure monitoring points",
        "gas flow measurement",
        "gas flow measurement points",
        "thermocouples",
        "real-time digital monitoring",
        "real time digital monitoring",
        "monitoring points",
        "instrumentation",
    ],
    "production.sensor_locations": [
        "pressure monitoring points",
        "gas flow measurement points",
        "sensor locations",
        "points of measurement",
        "located at",
        "multiple zones along reactor length",
        "combustion chamber interface",
        "inlet, outlet",
    ],
    "production.reactor_components": [
        "reactor components",
        "overall reactor length",
        "diameter and wall thickness",
        "feed inlet",
        "biochar discharge",
        "gas outlet",
        "combustion chamber interface",
        "insulation layers",
        "refractory lining",
        "integrated furnace",
        "gas burners",
        "pressure sensors",
        "thermocouples",
    ],
    "production.material_selection_justification": [
        "material selection",
        "selected materials",
        "materials used",
        "304 stainless steel",
        "reactor manufacturing",
        "equipment lifespan",
        "fabricated in 304 stainless steel",
        "corrosion resistance",
        "thermal resistance",
    ],
    "production.end_material_process_description": [
        "post-processing",
        "post processing",
        "cooling",
        "screening",
        "biochar discharge",
        "storage in big bags",
        "soil application",
        "end material",
        "biochar is regularly analyzed",
    ],

    # =========================================================
    # SAMPLING
    # =========================================================
    "sampling.batch_definition_days": [
        "24-hour production window",
        "24 hour production window",
        "hour production window",
        "within a maximum 24-hour production window",
        "within a maximum 24 hour production window",
        "production batch",
        "batch-level",
        "per production batch",
        "batch is defined as",
        "maximum 30 tonnes of biochar",
    ],
    "sampling.sampling_plan_defined": [
        "sampling plan",
        "sampling frequency",
        "analytical procedures",
        "per production batch",
        "at least once per production batch",
        "batch-level",
        "biochar samples are archived",
        "samples are archived",
        "operational and laboratory data are collected per batch",
        "sampling is conducted",
        "sampling frequency are included in the biochar annex",
    ],
    "sampling.method": [
        "method a",
        "method b",
        "sampling method a",
        "sampling method b",
    ],

    # =========================================================
    # FEEDSTOCK
    # =========================================================
    "feedstock.biomass_type": [
        "eucalyptus residues",
        "harvest residues",
        "branches",
        "tops",
        "leaves",
        "bark",
        "whole trees may also be used",
        "forestry residues",
        "downstream processing residues",
        "sawmill residue",
        "wood residues",
        "forest residues",
        "sawmill byproducts",
    ],
    "feedstock.pre_project_biomass_use": [
        "controlled open-air burning",
        "open burning",
        "burned in the field",
        "natural decay",
        "residue disposal",
        "controlled burning",
        "consumed as fuel",
        "would have been fully combusted",
        "no viable alternative commercial applications",
        "no other productive use",
        "not fit for use in building materials",
    ],
    "feedstock.feedstock_accounting_module_compliance": [
        "residue",
        "cut-off approach",
        "byproduct",
        "no land use change",
        "records are archived",
        "transport receipts",
        "harvest records",
        "cross-check against transport logs",
        "qa/qc procedures",
        "traceable feedstock records",
    ],
    "feedstock.moisture_measurement": [
        "moisture",
        "wet shredded biomass",
        "dry mass basis",
        "moisture content",
        "astm d1762-84",
        "moisture measurement",
    ],
    "feedstock.moisture_control_plan": [
        "moisture control plan",
        "feedstock drying plan",
        "moisture management plan",
        "target moisture range",
        "moisture control procedures",
    ],

    # =========================================================
    # STORAGE
    # =========================================================
    "methodology.storage_pathway": [
        "soil application",
        "applied to soil",
        "soil",
        "storage pathway",
        "storage in soil",
        "soil environments",
        "biochar spreading and storage in soil environments",
    ],
    "storage.storage_environment_stable": [
        "stable storage",
        "durable in soil",
        "soil application",
        "agricultural soil",
        "mixed into soil",
        "long-term stability in soil",
        "contaminant concentrations remain below thresholds",
        "post-application monitoring",
    ],
    "storage.soil.deployment_methods": [
        "deployment methods",
        "soil application",
        "applied back to the plantation area",
        "applied in eucalyptus fields",
        "application is supervised",
        "agronomic rates",
        "soil application at agronomic rates",
        "spreading",
        "incorporation",
        "injection",
    ],
    "storage.stockpiling_documented": [
        "stockpiling",
        "storage in big bags",
        "stored in big bags",
        "stockpiled before end use",
        "temporary storage prior to application",
    ],
    "storage.stockpiled_before_end_use": [
        "stockpiled before end use",
        "temporary storage prior to application",
        "stored before application",
        "stockpiling of biochar",
    ],
    "storage.soil.direct_application_evidence_pathway": [
        "direct soil application",
        "biochar soil application",
        "application only to suitable soils at agronomic rates",
        "baseline soil sampling before application",
        "post-application monitoring",
    ],

    # =========================================================
    # QUANTIFICATION / GHG
    # =========================================================
    "ghg_accounting.system_boundary_defined": [
        "system boundary",
        "project boundary",
        "boundaries",
        "figure 2",
        "sources, sinks and reservoirs",
        "ssrs",
        "included ssrs",
        "boundary includes",
        "operational emissions",
        "storage emissions",
        "biochar application",
        "embodied emissions",
        "transport emissions",
    ],
    "ghg_accounting.baseline_defined": [
        "baseline",
        "counterfactual",
        "open burning of residues",
        "absence of the project",
        "baseline scenario",
        "without the project",
        "would have been fully combusted",
        "consumed as fuel",
    ],
    "monitoring_reporting.uncertainty_method": [
        "uncertainty",
        "monte carlo",
        "variance propagation",
        "conservative parameter selection",
        "conservative assumptions",
        "conservative values",
        "sensitivity analysis",
        "uncertainty treatment",
    ],
    "quantification.input_variables": [
        "input variables",
        "model inputs",
        "assumptions",
        "limitations are disclosed",
        "equation 6.1",
        "ghg protocol",
        "organic carbon content",
        "fixed carbon",
        "yield",
        "biochar yield",
        "parameters used",
    ],
    "quantification.input_uncertainties": [
        "uncertainty",
        "monte carlo",
        "variance propagation",
        "conservative assumptions",
        "conservative values",
        "conservative parameter selection",
        "sensitivity analysis",
        "additional sensitivity analysis",
        "input uncertainty",
    ],
    "quantification.crediting_activity_boundaries": [
        "all steps involved in the product system",
        "collection and chipping",
        "production and post processing",
        "application in soil",
        "transport stages",
        "crediting activity boundaries",
        "construction/manufacturing boundaries",
        "operation boundaries",
        "closure/disposal boundaries",
        "activities leading to credits",
    ],
    "quantification.storage_emissions_accounted": [
        "storage emissions",
        "soil application emissions",
        "storage pathway emissions",
        "biochar storage - operational emissions",
        "biochar application",
        "storage emissions are included",
        "soil application is included in the boundary",
        "storage pathway included in lca",
    ],
    "biochar.characterization.chemical_analysis_performed": [
        "laboratory analysis",
        "chemical analysis",
        "biochar is regularly analyzed",
        "characterized using internationally recognized analytical standards",
        "iso/iec 17025",
    ],
    "biochar.characterization.lab_reports": [
        "lab report",
        "laboratory analysis",
        "accredited laboratories",
        "iso/iec 17025",
        "batch-linked through the project mrv system",
        "laboratory certificate",
    ],
    "biochar.characterization.required_measurements_complete": [
        "required measurements",
        "all relevant chemical properties",
        "batch-level elemental laboratory analysis",
        "fixed carbon",
        "ash content",
        "pahs",
        "ph",
        "cec",
        "required properties",
        "ultimate analysis",
        "proximate analysis",
    ],
    "biochar.characterization.measurement_values": [
        "measurement values",
        "organic carbon content",
        "h/corg",
        "o/c",
        "carbon content",
        "fixed carbon",
        "ash content",
        "paHs",
        "ph",
        "cec",
        "measured and reported",
        "parameters measured",
    ],
    "biochar.characterization.approach_description": [
        "characterization approach",
        "sampling frequency",
        "methodology",
        "batch traceability",
        "accredited laboratories",
        "standardized analytical methods",
    ],
    "biochar.characterization.ongoing_monitoring_plan": [
        "ongoing monitoring",
        "regularly analyzed",
        "annual emission testing",
        "biochar annex",
        "monitoring plan",
        "annual laboratory analysis frequency",
    ],
    "biochar.characterization.contaminant_testing": [
        "heavy metals",
        "contaminants",
        "pah",
        "epa 8270d",
        "en 16181",
        "din 38414-s4",
        "each batch is tested for contaminants",
        "contaminant testing results are archived",
    ],
    "biochar.characterization.contaminant_testing_frequency": [
        "contaminant analysis per 100 tonnes",
        "minimum annual laboratory analysis frequency",
        "proximate/ultimate analysis per batch",
        "full contaminant analysis per",
    ],
    "product.standard_compliance": [
        "astm",
        "epa 8270d",
        "en 16181",
        "product standard",
        "standard compliance",
        "internationally recognized analytical standards",
        "isometric bicrs",
    ],
    "product.certification_scheme": [
        "world biochar certificate",
        "ebc",
        "isometric bicrs",
        "puro standard",
        "certification scheme",
        "protocol",
    ],

    # =========================================================
    # TRACEABILITY
    # =========================================================
    "traceability.chain_of_custody": [
        "chain of custody",
        "traceability",
        "prevent double counting",
        "coc",
        "chain-of-custody",
    ],
    "traceability.records_archived": [
        "records are archived",
        "minimum of 20 years",
        "samples are archived",
        "secure digital systems",
        "regular backups",
        "batch-linked",
        "archived and made available for audit",
    ],
    "traceability.chain_of_custody_diagram": [
        "chain of custody diagram",
        "diagrammatic representation of chain of custody",
        "flow diagram of custody",
        "coc diagram",
    ],

    # =========================================================
    # EMISSIONS
    # =========================================================
    "emissions.stack_monitoring_method": [
        "annual emission testing",
        "stack emissions",
        "air emissions",
        "emissions monitoring",
        "atmospheric emissions",
        "stack monitoring",
        "periodic stack emissions testing",
    ],
    "emissions.testing_frequency": [
        "annual emission testing",
        "annual",
        "periodic testing",
        "regular testing",
        "testing frequency",
    ],
    "emissions.pyrolysis_gas_end_use_approach": [
        "combustion gases burned in an integrated furnace",
        "controlled combustion of pyrolysis gases",
        "gas burners",
        "integrated furnace",
        "heat is partially reused to sustain the process",
        "combusted in integrated furnace",
        "sealed combustion system",
        "gas recovery and sealed combustion",
    ],
    "emissions.emissions_control_system": [
        "controlled combustion",
        "integrated furnace",
        "gas burners",
        "controlled combustion systems for process gases",
        "thermal control",
        "sealed combustion system",
        "real-time digital monitoring",
    ],

    # =========================================================
    # MANAGEMENT
    # =========================================================
    "management.adaptive_management_plan": [
        "adaptive management",
        "adaptive management framework",
        "review operational assumptions",
        "revise monitoring approach",
        "corrective action framework",
    ],
    "management.information_sharing_plan": [
        "information sharing",
        "communication",
        "report findings",
        "share results",
        "internal review",
        "information sharing plan",
    ],
    "management.emergency_response_plan": [
        "emergency response",
        "incident response",
        "contingency",
        "response procedures",
        "emergency response plan",
    ],
    "management.pause_or_stop_conditions": [
        "pause",
        "stop operations",
        "suspend operations",
        "conditions for resumption",
        "operations may be paused",
        "pause or stop conditions",
    ],
    "management.monitoring_triggers": [
        "trigger",
        "threshold",
        "exceedance",
        "review points",
        "conditions for resumption",
        "corrective actions",
        "monitoring obligations",
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
        "feedstock.moisture_control_plan",
    ],
    "storage": [
        "methodology.storage_pathway",
        "storage.storage_environment_stable",
        "storage.soil.deployment_methods",
        "storage.stockpiling_documented",
        "storage.stockpiled_before_end_use",
        "storage.soil.direct_application_evidence_pathway",
    ],
    "quantification": [
        "ghg_accounting.system_boundary_defined",
        "ghg_accounting.baseline_defined",
        "monitoring_reporting.uncertainty_method",
        "quantification.input_variables",
        "quantification.input_uncertainties",
        "quantification.crediting_activity_boundaries",
        "quantification.storage_emissions_accounted",
        "biochar.characterization.chemical_analysis_performed",
        "biochar.characterization.lab_reports",
        "biochar.characterization.required_measurements_complete",
        "biochar.characterization.measurement_values",
        "biochar.characterization.approach_description",
        "biochar.characterization.ongoing_monitoring_plan",
        "biochar.characterization.contaminant_testing",
        "biochar.characterization.contaminant_testing_frequency",
        "product.standard_compliance",
        "product.certification_scheme",
    ],
    "traceability": [
        "traceability.chain_of_custody",
        "traceability.records_archived",
        "traceability.chain_of_custody_diagram",
    ],
    "emissions": [
        "emissions.stack_monitoring_method",
        "emissions.testing_frequency",
        "emissions.pyrolysis_gas_end_use_approach",
        "emissions.emissions_control_system",
    ],
    "management": [
        "management.adaptive_management_plan",
        "management.information_sharing_plan",
        "management.emergency_response_plan",
        "management.pause_or_stop_conditions",
        "management.monitoring_triggers",
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
        "management": _build_domain_context_from_hits(project_hits, methodology_context, "management"),
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
        ("management_mapper", run_management_mapper, "management"),
        # Phase 3: numeric values from biochar characterization (H/C, O/C, contaminants)
        ("biochar_characterization_mapper", run_biochar_characterization_mapper, "production"),
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
