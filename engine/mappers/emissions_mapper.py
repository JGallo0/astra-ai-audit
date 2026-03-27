import re
from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    filter_fields_by_paths,
    merge_normalized_fields,
    normalize_domain_fields,
    parse_extraction_payload,
    upsert_field,
)


EMISSIONS_PREFIXES = [
    "emissions.",
    "emissions_testing.",
]

EMISSIONS_EXTRA_PATHS = [
    "emissions.stack_monitoring_method",
    "emissions.testing_frequency",
    "emissions.pyrolysis_gas_end_use_approach",
    "emissions.emissions_control_system",
]


def get_fields() -> List[Dict[str, Any]]:
    prefixed = filter_fields_by_prefixes(EXTRACTION_FIELDS, EMISSIONS_PREFIXES)
    extra = filter_fields_by_paths(EXTRACTION_FIELDS, EMISSIONS_EXTRA_PATHS)

    merged = {f["path"]: f for f in prefixed}
    for f in extra:
        merged[f["path"]] = f

    return list(merged.values())


def _instructions() -> str:
    return """
Focus on emissions monitoring and pyrolysis gas end-use.

Important interpretation rules:
- Count emissions.stack_monitoring_method when the project explicitly describes
  stack emissions testing, emissions monitoring method, annual emissions testing,
  or equivalent atmospheric emissions monitoring.
- Count emissions.testing_frequency when the project explicitly states annual,
  periodic, batch-based, or other recurring testing frequency for emissions.
- Count emissions.pyrolysis_gas_end_use_approach when the project explicitly describes
  what happens to pyrolysis gases (e.g. burned in integrated furnace, combusted,
  recycled, flared, or otherwise accounted for).
- Count emissions.emissions_control_system when the project explicitly describes
  controlled combustion, integrated furnace, gas burners, or an emissions control system.
- Prefer null over false when unclear.
"""


def sanitize_emissions_fields(
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    value = field_map.get("emissions.stack_monitoring_method", {}).get("value")

    if isinstance(value, str) and value.lower() in {"true", "false"}:
        field_map.pop("emissions.stack_monitoring_method", None)

    return list(field_map.values())


def apply_local_heuristics(
    project_context: str,
    methodology_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    project_text = (project_context or "").lower()
    methodology_text = (methodology_context or "").lower()
    combined_text = f"{project_text}\n{methodology_text}"

    field_map = {item["path"]: dict(item) for item in normalized_fields}

    # ------------------------------------------------------------
    # emissions.stack_monitoring_method
    # ------------------------------------------------------------
    current = field_map.get("emissions.stack_monitoring_method", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"annual emission testing", combined_text)
            or re.search(r"emissions are maintained within applicable regulatory limits", combined_text)
            or re.search(r"air emissions", combined_text)
            or re.search(r"stack emissions", combined_text)
        ):
            upsert_field(
                field_map,
                path="emissions.stack_monitoring_method",
                value="periodic_stack_emissions_testing",
                evidence="Heuristic match: annual emissions testing / atmospheric emissions monitoring is explicitly described.",
                extractor="emissions_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # emissions.testing_frequency
    # ------------------------------------------------------------
    current = field_map.get("emissions.testing_frequency", {}).get("value")
    if current in (None, False, "", []):
        if re.search(r"annual emission testing", combined_text):
            upsert_field(
                field_map,
                path="emissions.testing_frequency",
                value="annual",
                evidence="Heuristic match: annual emission testing explicitly referenced.",
                extractor="emissions_mapper",
                fill_method="heuristic",
                confidence=0.96,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif re.search(r"periodic review|periodic testing|regular testing", combined_text):
            upsert_field(
                field_map,
                path="emissions.testing_frequency",
                value="periodic",
                evidence="Heuristic match: periodic/regular emissions testing explicitly referenced.",
                extractor="emissions_mapper",
                fill_method="heuristic",
                confidence=0.82,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # emissions.pyrolysis_gas_end_use_approach
    # ------------------------------------------------------------
    current = field_map.get("emissions.pyrolysis_gas_end_use_approach", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"combustion gases burned in an integrated furnace", combined_text)
            or re.search(r"controlled combustion of pyrolysis gases", combined_text)
            or re.search(r"gas burners", combined_text)
            or re.search(r"heat is partially reused to sustain the process", combined_text)
        ):
            upsert_field(
                field_map,
                path="emissions.pyrolysis_gas_end_use_approach",
                value="combusted_in_integrated_furnace",
                evidence="Heuristic match: pyrolysis/combustion gases are explicitly described as burned/combusted in an integrated furnace or controlled burner system.",
                extractor="emissions_mapper",
                fill_method="heuristic",
                confidence=0.94,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # emissions.emissions_control_system
    # ------------------------------------------------------------
    current = field_map.get("emissions.emissions_control_system", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"controlled combustion", combined_text)
            or re.search(r"integrated furnace", combined_text)
            or re.search(r"gas burners", combined_text)
            or re.search(r"controlled combustion systems for process gases", combined_text)
            or re.search(r"thermal control", combined_text)
        ):
            upsert_field(
                field_map,
                path="emissions.emissions_control_system",
                value=True,
                evidence="Heuristic match: controlled combustion / integrated furnace / gas burner emissions control system is explicitly described.",
                extractor="emissions_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))


def run_emissions_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()

    if not fields:
        return {
            "normalized_fields": [],
            "raw_extraction": {"fields": []},
        }

    prompt = build_domain_prompt(
        domain_name="emissions",
        fields=fields,
        project_context=project_context,
        methodology_context=methodology_context,
        domain_instructions=_instructions(),
    )

    raw = ai_client(prompt)
    payload = parse_extraction_payload(raw)

    normalized = normalize_domain_fields(
        extracted_payload=payload,
        fields=fields,
        extractor_name="emissions_mapper",
        fill_method="llm",
    )

    normalized = sanitize_emissions_fields(normalized)

    normalized = apply_local_heuristics(
        project_context=project_context,
        methodology_context=methodology_context,
        normalized_fields=normalized,
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
