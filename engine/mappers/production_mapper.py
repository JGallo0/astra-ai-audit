# engine/mappers/production_mapper.py

import re
from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    merge_normalized_fields,
    normalize_domain_fields,
    parse_extraction_payload,
    upsert_field,
)


PRODUCTION_PREFIXES = ["production."]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_prefixes(EXTRACTION_FIELDS, PRODUCTION_PREFIXES)


def _instructions() -> str:
    return """
Focus on production system evidence:
- pyrolysis technology
- reactor design / engineering package
- maintenance plan / schedule
- sensor inventory and locations
- reactor components and material selection
Strong signals include:
PFD, P&ID, reactor drawing, process flow diagram, engineering design package,
maintenance schedule, preventive maintenance, sensor list, instrumentation map.
"""


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    if field_map.get("production.reactor_design_diagram", {}).get("value") is not True:
        if re.search(r"\b(pfd|p&id|engineering design package|reactor drawing|process flow diagram|process schematic|layout drawing)\b", text):
            upsert_field(
                field_map,
                path="production.reactor_design_diagram",
                value=True,
                evidence="Heuristic match: PFD/P&ID/reactor drawing/process flow evidence found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    if field_map.get("production.engineering_design_diagram", {}).get("value") is not True:
        if re.search(r"\b(engineering design package|pfd|p&id|process flow diagram|process schematic|layout drawing)\b", text):
            upsert_field(
                field_map,
                path="production.engineering_design_diagram",
                value=True,
                evidence="Heuristic match: engineering design package or process diagram evidence found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.89,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    if field_map.get("production.maintenance_plan", {}).get("value") is not True:
        if re.search(r"(maintenance (plan|schedule|routine))|(preventive maintenance)|(daily.{0,20}inspection)|(weekly.{0,20}inspection)|(monthly.{0,20}inspection)|(annual.{0,20}servicing)", text, re.DOTALL):
            upsert_field(
                field_map,
                path="production.maintenance_plan",
                value=True,
                evidence="Heuristic match: maintenance schedule/routine/inspection pattern identified.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.87,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    if field_map.get("production.maintenance_schedule", {}).get("value") is not True:
        if re.search(r"(maintenance schedule)|(daily.{0,20}inspection)|(weekly.{0,20}inspection)|(monthly.{0,20}inspection)|(annual.{0,20}servicing)", text, re.DOTALL):
            upsert_field(
                field_map,
                path="production.maintenance_schedule",
                value=True,
                evidence="Heuristic match: explicit maintenance schedule or inspection/service cadence identified.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.86,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))


def run_production_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    prompt = build_domain_prompt(
        domain_name="production",
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
        extractor_name="production_mapper",
        fill_method="llm",
    )
    normalized = apply_local_heuristics(project_context, normalized)

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
