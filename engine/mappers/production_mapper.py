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
- reactor / kiln configuration
- engineering package / reactor design evidence
- maintenance plan / maintenance schedule
- instrumentation and monitoring equipment
- process parameters and operating setup

Important interpretation rules:
- Count production.pyrolysis_technology when the project explicitly names the technology
  (e.g. BST-30, rectangular kilns, continuous reactor, pyrolysis reactor).
- Count reactor/engineering diagram fields not only for explicit PFD/P&ID wording, but also when the
  project clearly references a technical annex, engineering package, layout/map, or detailed engineered system
  description with sensors, dimensions, and controlled process design.
- Count maintenance_plan / maintenance_schedule when the project describes structured operational routines,
  annual testing, preventive monitoring, inspection cadence, or formal process-control procedures.
- The project is pre-operational, so do not infer measured performance from planned equipment.

Evidence grading:
- strong: explicit PFD/P&ID, annex, drawing, engineering package, maintenance schedule wording
- moderate: clear technical system description with sensors, dimensions, monitoring, annual testing
- weak: vague technical description only
"""


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    # ------------------------------------------------------------------
    # production.pyrolysis_technology
    # ------------------------------------------------------------------
    current = field_map.get("production.pyrolysis_technology", {}).get("value")
    if current in (None, "", []):
        if re.search(r"\bbst-30\b", text) and re.search(r"\b(pyrolysis reactor|continuous pyrolysis|reactor)\b", text):
            upsert_field(
                field_map,
                path="production.pyrolysis_technology",
                value="BST-30 continuous rotary pyrolysis reactor",
                evidence="Heuristic match: explicit BST-30 pyrolysis reactor wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif re.search(r"\brectangular kilns?\b", text):
            upsert_field(
                field_map,
                path="production.pyrolysis_technology",
                value="rectangular kilns with gas burners and thermal control",
                evidence="Heuristic match: project explicitly describes rectangular kilns with controlled thermal operation.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.88,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # production.reactor_design_diagram
    # ------------------------------------------------------------------
    current = field_map.get("production.reactor_design_diagram", {}).get("value")
    if current is not True:
        # strong case: explicit diagram language
        strong_patterns = [
            r"\bpfd\b",
            r"\bp&id\b",
            r"process flow diagram",
            r"engineering design package",
            r"reactor drawing",
            r"layout drawing",
            r"technical annex",
            r"reference map",
        ]
        moderate_patterns = [
            r"thermocouples",
            r"pressure sensors",
            r"real-time digital monitoring",
            r"controlled incomplete combustion",
            r"\b6×3×3\b",
            r"\b6x3x3\b",
            r"batch capacity",
        ]

        if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in strong_patterns):
            upsert_field(
                field_map,
                path="production.reactor_design_diagram",
                value=True,
                evidence="Heuristic match: explicit diagram / annex / engineering-reference wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="referenced_attachment",
            )
        elif sum(bool(re.search(p, text, re.IGNORECASE | re.DOTALL)) for p in moderate_patterns) >= 2:
            upsert_field(
                field_map,
                path="production.reactor_design_diagram",
                value=True,
                evidence="Heuristic match: detailed engineered-system description found (dimensions, sensors, controlled operation).",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.76,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )

    # ------------------------------------------------------------------
    # production.engineering_design_diagram
    # ------------------------------------------------------------------
    current = field_map.get("production.engineering_design_diagram", {}).get("value")
    if current is not True:
        if re.search(
            r"\b(pfd|p&id|engineering design package|process flow diagram|layout drawing|technical annex)\b",
            text,
            re.IGNORECASE | re.DOTALL,
        ):
            upsert_field(
                field_map,
                path="production.engineering_design_diagram",
                value=True,
                evidence="Heuristic match: explicit engineering-diagram / annex wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.88,
                evidence_strength="strong",
                evidence_mode="referenced_attachment",
            )

    # ------------------------------------------------------------------
    # production.maintenance_plan
    # ------------------------------------------------------------------
    current = field_map.get("production.maintenance_plan", {}).get("value")
    if current is not True:
        strong_patterns = [
            r"maintenance plan",
            r"maintenance schedule",
            r"preventive maintenance",
            r"routine maintenance",
        ]
        moderate_patterns = [
            r"annual emission testing",
            r"real-time digital monitoring",
            r"thermocouples",
            r"pressure sensors",
            r"process monitoring",
            r"mrv",
            r"operational procedures",
        ]

        if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in strong_patterns):
            upsert_field(
                field_map,
                path="production.maintenance_plan",
                value=True,
                evidence="Heuristic match: explicit maintenance-plan wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif sum(bool(re.search(p, text, re.IGNORECASE | re.DOTALL)) for p in moderate_patterns) >= 3:
            upsert_field(
                field_map,
                path="production.maintenance_plan",
                value=True,
                evidence="Heuristic match: structured operational monitoring and annual testing strongly imply a maintenance plan.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.75,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )

    # ------------------------------------------------------------------
    # production.maintenance_schedule
    # ------------------------------------------------------------------
    current = field_map.get("production.maintenance_schedule", {}).get("value")
    if current is not True:
        if re.search(
            r"(maintenance schedule)|(annual emission testing)|(real-time digital monitoring)|(process monitoring)",
            text,
            re.IGNORECASE | re.DOTALL,
        ):
            upsert_field(
                field_map,
                path="production.maintenance_schedule",
                value=True,
                evidence="Heuristic match: project describes recurring operational monitoring/testing consistent with a maintenance schedule.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.73,
                evidence_strength="moderate",
                evidence_mode="inferred",
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

    normalized = apply_local_heuristics(
        project_context=project_context,
        normalized_fields=normalized,
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
