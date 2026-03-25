# engine/mappers/__init__.py

from typing import Any, Dict, List

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


DOMAIN_HINTS = {
    "eligibility": [
        "eligible",
        "eligibility",
        "isometric",
        "biochar",
        "net negative",
        "negative carbon footprint",
        "environmental additionality",
        "regulatory additionality",
        "common practice",
        "financial additionality",
        "durability",
        "durability option",
        "200-year",
        "1000-year",
        "threshold",
        "project removals",
        "emissions",
        "lca",
        "kgco2eq",
        "tco2e/t",
        "pathway",
        "production subpathway",
    ],
    "additionality": [
        "additionality",
        "financial additionality",
        "regulatory additionality",
        "environmental additionality",
        "common practice",
        "baseline",
        "counterfactual",
        "irr",
        "carbon credit revenues",
        "economic barriers",
        "sensitive to carbon credit pricing",
    ],
    "durability": [
        "durability",
        "durability option",
        "200-year",
        "1000-year",
        "permanence",
        "stable storage",
        "h/corg",
        "soil temperature",
        "reversal",
        "buffer pool",
        "risk of reversal",
    ],
    "production": [
        "production",
        "pyrolysis",
        "reactor",
        "bst-30",
        "rectangular kilns",
        "engineering design package",
        "pfd",
        "p&id",
        "process flow diagram",
        "layout drawing",
        "reactor drawing",
        "maintenance plan",
        "maintenance schedule",
        "daily inspection",
        "weekly inspection",
        "annual servicing",
        "annual emission testing",
        "sensor",
        "temperature sensors",
        "pressure sensors",
        "pressure monitoring points",
        "gas flow measurement",
        "thermocouples",
        "monitoring points",
        "real-time digital monitoring",
        "controlled incomplete combustion",
        "batch capacity",
    ],
    "sampling": [
        "sampling",
        "sampling plan",
        "sampling frequency",
        "method a",
        "method b",
        "production batch",
        "batch-level",
        "per production batch",
        "at least once per production batch",
        "24-hour production window",
        "hour production window",
        "composite samples",
        "sample monitoring",
        "biochar samples are archived",
        "analytical procedures",
    ],
    "feedstock": [
        "feedstock",
        "biomass",
        "eucalyptus residues",
        "harvest residues",
        "branches",
        "tops",
        "leaves",
        "bark",
        "pre-project",
        "controlled burning",
        "open burning",
        "moisture",
    ],
    "storage": [
        "storage",
        "soil application",
        "applied to soil",
        "storage pathway",
        "deployment methods",
        "stockpiling",
        "soil",
        "storage environment",
        "stable storage",
        "application area",
    ],
    "quantification": [
        "quantification",
        "lca",
        "openlca",
        "ecoinvent",
        "boundary",
        "system boundary",
        "uncertainty",
        "monte carlo",
        "variance propagation",
        "measurement",
        "measurement values",
        "biochar characterization",
        "lab report",
        "iso/iec 17025",
        "required measurements",
        "product standard",
        "co2eq",
        "ghg statement",
    ],
    "traceability": [
        "traceability",
        "chain of custody",
        "records archived",
        "archived",
        "batch",
        "lot",
        "delivery note",
        "tracking",
        "transport records",
        "document trail",
        "carbonfuture",
        "scada",
    ],
}


def _split_context_lines(project_context: str) -> List[str]:
    if not project_context:
        return []
    lines = [line.strip() for line in project_context.splitlines()]
    return [line for line in lines if line]


def _score_line_for_hints(line: str, hints: List[str]) -> int:
    lowered = line.lower()
    score = 0
    for hint in hints:
        if hint.lower() in lowered:
            score += 1
    return score


def _build_domain_context(
    project_context: str,
    methodology_context: str,
    domain_name: str,
    max_lines: int = 40,
) -> str:
    """
    Build a domain-focused context from the global project_context by keeping
    the lines that are most relevant to the domain hints.

    This is intentionally simple and deterministic for v1:
    - keep lines that match domain hints
    - preserve order
    - append methodology context at the end for interpretation
    """
    hints = DOMAIN_HINTS.get(domain_name, [])
    lines = _split_context_lines(project_context)

    scored_lines = []
    for idx, line in enumerate(lines):
        score = _score_line_for_hints(line, hints)
        if score > 0:
            scored_lines.append((idx, score, line))

    # Keep the strongest hits, but preserve original order afterward
    scored_lines.sort(key=lambda x: (-x[1], x[0]))
    top = scored_lines[:max_lines]
    top.sort(key=lambda x: x[0])

    selected_lines = [line for _, _, line in top]

    # Fallback: if domain-specific filtering found too little, keep the first chunk
    if len(selected_lines) < 8:
        fallback_lines = lines[:max_lines]
        for line in fallback_lines:
            if line not in selected_lines:
                selected_lines.append(line)
            if len(selected_lines) >= max_lines:
                break

    project_block = "\n".join(selected_lines).strip()
    methodology_block = (methodology_context or "").strip()

    return f"""
DOMAIN: {domain_name}

PROJECT EVIDENCE (domain-focused):
{project_block}

METHODOLOGY CONTEXT:
{methodology_block}
""".strip()


def _build_domain_contexts(
    project_context: str,
    methodology_context: str,
) -> Dict[str, str]:
    return {
        "eligibility": _build_domain_context(project_context, methodology_context, "eligibility"),
        "additionality": _build_domain_context(project_context, methodology_context, "additionality"),
        "durability": _build_domain_context(project_context, methodology_context, "durability"),
        "production": _build_domain_context(project_context, methodology_context, "production"),
        "sampling": _build_domain_context(project_context, methodology_context, "sampling"),
        "feedstock": _build_domain_context(project_context, methodology_context, "feedstock"),
        "storage": _build_domain_context(project_context, methodology_context, "storage"),
        "quantification": _build_domain_context(project_context, methodology_context, "quantification"),
        "traceability": _build_domain_context(project_context, methodology_context, "traceability"),
        "global": project_context or "",
    }


def run_mapper_pipeline(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    raw_bundle: Dict[str, Any] = {}
    collected: List[Dict[str, Any]] = []

    domain_contexts = _build_domain_contexts(
        project_context=project_context,
        methodology_context=methodology_context,
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
    ]

    for name, fn, domain_key in mapper_runs:
        domain_project_context = domain_contexts.get(domain_key, project_context)

        result = fn(
            ai_client=ai_client,
            project_context=domain_project_context,
            methodology_context=methodology_context,
        )

        raw_bundle[name] = {
            "domain_key": domain_key,
            "project_context_used": domain_project_context,
            "raw_extraction": result.get("raw_extraction", {"fields": []}),
        }

        collected.extend(result.get("normalized_fields", []))

    merged = merge_normalized_fields(collected)
    missing_paths = find_missing_paths(merged, EXTRACTION_FIELDS)

    fallback_result = run_fallback_mapper(
        ai_client=ai_client,
        project_context=domain_contexts["global"],
        methodology_context=methodology_context,
        missing_paths=missing_paths,
    )

    raw_bundle["fallback_mapper"] = {
        "domain_key": "global",
        "project_context_used": domain_contexts["global"],
        "raw_extraction": fallback_result.get("raw_extraction", {"fields": []}),
    }

    merged = merge_normalized_fields(
        merged + fallback_result.get("normalized_fields", [])
    )

    return {
        "normalized_fields": merged,
        "raw_extraction_bundle": raw_bundle,
    }
