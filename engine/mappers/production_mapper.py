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
- Count reactor/engineering diagram fields for explicit PFD/P&ID wording, engineering package,
  layout drawings, technical annex references, or a clearly engineered system description with
  dimensions, sensors, and process-control points.
- Count maintenance fields when the project describes structured maintenance routines, recurring inspections,
  calibration schedules, annual testing, or clearly organized operational maintenance procedures.
- Count sensor inventory / sensor locations when the project explicitly lists sensor types, locations,
  or monitoring points (e.g. temperature sensors, pressure monitoring points, gas-flow measurement points).
- The project may be pre-operational. Do not require real measured performance to fill engineering fields.
"""


def sanitize_production_fields(
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    value = field_map.get("production.pyrolysis_technology", {}).get("value")

    if isinstance(value, str) and value.lower() in {"true", "false"}:
        field_map.pop("production.pyrolysis_technology", None)

    invalid_generic_values = {
        "biochar",
        "biochar production",
        "production of biochar",
        "biochar system",
        "biochar technology",
        "carbon removal technology",
        "pyrolysis",
    }

    if isinstance(value, str) and value.strip().lower() in invalid_generic_values:
        field_map.pop("production.pyrolysis_technology", None)

    return list(field_map.values())


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

    invalid_string_values = {
        "",
        "pyrolysis",
    }

    if isinstance(current, str):
        current_normalized = current.strip().lower()
        is_invalid = current_normalized in invalid_string_values
    else:
        is_invalid = current in (None, [])

    if is_invalid:
        if re.search(r"\bbst-30\b", text) and re.search(r"\b(pyrolysis reactor|continuous pyrolysis|continuous reactor|reactor)\b", text):
            upsert_field(
                field_map,
                path="production.pyrolysis_technology",
                value="BST-30 continuous rotary pyrolysis reactor",
                evidence="Heuristic match: explicit BST-30 pyrolysis reactor wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.94,
                evidence_strength="strong",
                evidence_mode="direct",
            )

        elif re.search(r"\b(continuous pyrolysis|continuous reactor|pyrolysis reactor|rotary reactor)\b", text):
            upsert_field(
                field_map,
                path="production.pyrolysis_technology",
                value="continuous pyrolysis reactor",
                evidence="Heuristic match: explicit continuous pyrolysis / reactor wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.88,
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
                confidence=0.89,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # production.system_description  (R-NK7R-0, R-7X0X-0)
    # ------------------------------------------------------------------
    current = field_map.get("production.system_description", {}).get("value")
    if not current:
        # Look for narrative descriptions of the production system
        desc_patterns = [
            r"(?:the\s+project\s+(?:uses?|utilizes?|operates?|employs?))\s+(.{30,250})",
            r"(?:biochar\s+is\s+(?:produced?|generated?|made?))\s+(?:using|via|through|by)\s+(.{20,200})",
            r"(?:pyrolysis\s+(?:system|process|technology|reactor))\s+(?:is|consists?|operates?)\s+(.{20,200})",
            r"(?:the\s+facility|the\s+plant|the\s+system)\s+(?:consists?|comprises?|uses?)\s+(.{20,200})",
            r"(?:production\s+(?:system|process|technology))[:\s]+(.{20,250})",
        ]
        for pattern in desc_patterns:
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if m:
                desc = re.sub(r"\s+", " ", m.group(1)).strip()[:300]
                if len(desc) > 20:
                    upsert_field(
                        field_map,
                        path="production.system_description",
                        value=desc,
                        evidence=f"Heuristic: system description extracted.",
                        extractor="production_mapper",
                        fill_method="heuristic",
                        confidence=0.72,
                        evidence_strength="moderate",
                        evidence_mode="direct",
                    )
                    break

    # ------------------------------------------------------------------
    # production.reactor_design_diagram
    # ------------------------------------------------------------------
    current = field_map.get("production.reactor_design_diagram", {}).get("value")
    if current is not True:
        strong_patterns = [
            r"\bpfd\b",
            r"\bp&id\b",
            r"process flow diagrams?",
            r"piping and instrumentation diagrams?",
            r"engineering design package",
            r"reactor drawing",
            r"layout drawings?",
            r"technical annex",
        ]
        moderate_patterns = [
            r"temperature sensors?",
            r"pressure monitoring points?",
            r"gas flow measurement",
            r"thermocouples",
            r"pressure sensors",
            r"real-time digital monitoring",
            r"controlled incomplete combustion",
            r"batch capacity",
            r"\b6x3x3\b",
            r"\b6×3×3\b",
        ]

        if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in strong_patterns):
            upsert_field(
                field_map,
                path="production.reactor_design_diagram",
                value=True,
                evidence="Heuristic match: explicit PFD/P&ID/layout/engineering-package wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="referenced_attachment",
            )
        elif sum(bool(re.search(p, text, re.IGNORECASE | re.DOTALL)) for p in moderate_patterns) >= 3:
            upsert_field(
                field_map,
                path="production.reactor_design_diagram",
                value=True,
                evidence="Heuristic match: detailed engineered-system description found (dimensions, sensors, monitoring points, controlled operation).",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.80,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )

    # ------------------------------------------------------------------
    # production.engineering_design_diagram
    # ------------------------------------------------------------------
    current = field_map.get("production.engineering_design_diagram", {}).get("value")
    if current is not True:
        if re.search(
            r"\b(pfd|p&id|process flow diagrams?|piping and instrumentation diagrams?|engineering design package|layout drawings?|technical annex)\b",
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
                confidence=0.92,
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
            r"the maintenance plan is structured around",
            r"maintenance schedule summary",
            r"preventive maintenance",
            r"routine maintenance",
        ]
        moderate_patterns = [
            r"annual emission testing",
            r"calibration",
            r"semi-annual calibration",
            r"real-time digital monitoring",
            r"process monitoring",
            r"inspection",
            r"daily inspection",
            r"weekly inspection",
            r"mrv",
        ]

        if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in strong_patterns):
            upsert_field(
                field_map,
                path="production.maintenance_plan",
                value=True,
                evidence="Heuristic match: explicit maintenance-plan wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.94,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif sum(bool(re.search(p, text, re.IGNORECASE | re.DOTALL)) for p in moderate_patterns) >= 3:
            upsert_field(
                field_map,
                path="production.maintenance_plan",
                value=True,
                evidence="Heuristic match: structured inspections, calibration, testing, and process-monitoring language imply a maintenance plan.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.81,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )

    # ------------------------------------------------------------------
    # production.maintenance_schedule
    # ------------------------------------------------------------------
    current = field_map.get("production.maintenance_schedule", {}).get("value")
    if current is not True:
        schedule_patterns = [
            r"maintenance schedule",
            r"maintenance schedule summary",
            r"daily inspection",
            r"weekly inspection",
            r"monthly inspection",
            r"annual servicing",
            r"semi-annual calibration",
            r"annual emission testing",
        ]
        if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in schedule_patterns):
            upsert_field(
                field_map,
                path="production.maintenance_schedule",
                value=True,
                evidence="Heuristic match: explicit recurring inspection/calibration/testing cadence found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.91,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # production.sensor_inventory
    # ------------------------------------------------------------------
    current = field_map.get("production.sensor_inventory", {}).get("value")
    if current is not True:
        inventory_patterns = [
            r"temperature sensors?",
            r"pressure monitoring points?",
            r"gas flow measurement",
            r"thermocouples",
            r"pressure sensors",
            r"real-time digital monitoring",
        ]
        if sum(bool(re.search(p, text, re.IGNORECASE | re.DOTALL)) for p in inventory_patterns) >= 2:
            upsert_field(
                field_map,
                path="production.sensor_inventory",
                value=True,
                evidence="Heuristic match: explicit sensor/instrumentation inventory elements found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # production.sensor_locations
    # ------------------------------------------------------------------
    current = field_map.get("production.sensor_locations", {}).get("value")
    if current is not True:
        location_patterns = [
            r"pressure monitoring points?",
            r"gas flow measurement",
            r"sensor locations?",
            r"points? of measurement",
            r"located at",
        ]
        if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in location_patterns):
            upsert_field(
                field_map,
                path="production.sensor_locations",
                value=True,
                evidence="Heuristic match: explicit monitoring points / measurement-location wording found.",
                extractor="production_mapper",
                fill_method="heuristic",
                confidence=0.84,
                evidence_strength="moderate",
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

    normalized = sanitize_production_fields(normalized)

    normalized = apply_local_heuristics(
        project_context=project_context,
        normalized_fields=normalized,
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
