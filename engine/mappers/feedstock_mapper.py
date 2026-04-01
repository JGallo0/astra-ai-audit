# engine/mappers/feedstock_mapper.py

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


FEEDSTOCK_PREFIXES = ["feedstock."]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_prefixes(EXTRACTION_FIELDS, FEEDSTOCK_PREFIXES)


def _instructions() -> str:
    return """
Focus on feedstock evidence:
- biomass type
- pre-project use
- accounting module or classification
- feedstock origin and source locations
- moisture measurement / control

Important interpretation rules:
- Count feedstock.source_locations when the project explicitly identifies source geography,
  sawmills, counties, forests, regions, sourcing radius, or named sourcing locations.
- Count feedstock.moisture_measurement when moisture content, moisture factor, drying basis,
  or moisture-related adjustment is explicitly described.
- Do not require exact coordinates. Named operational geographies are enough.
Be conservative.
"""


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    # ------------------------------------------------------------
    # feedstock.source_locations
    # ------------------------------------------------------------
    current_locations = field_map.get("feedstock.source_locations", {}).get("value")

    if current_locations in (None, "", [], False):
        source_locations = []

        location_patterns = [
            r"\bScotia,\s*CA\b",
            r"\bHumboldt County\b",
            r"\bCalifornia\b",
            r"\bHumboldt Sawmill Company\b",
            r"\bsawmill\b",
            r"\bsawmills\b",
        ]

        for pattern in location_patterns:
            matches = re.findall(pattern, project_context or "", re.IGNORECASE)
            for match in matches:
                cleaned = str(match).strip()
                if cleaned and cleaned not in source_locations:
                    source_locations.append(cleaned)

        if source_locations:
            upsert_field(
                field_map,
                path="feedstock.source_locations",
                value=source_locations,
                evidence="Heuristic match: feedstock sourcing locations identified from explicit geography and sawmill references in project text.",
                extractor="feedstock_mapper",
                fill_method="heuristic",
                confidence=0.88,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # feedstock.moisture_measurement
    # ------------------------------------------------------------
    current_moisture = field_map.get("feedstock.moisture_measurement", {}).get("value")

    if current_moisture in (None, "", [], False):
        if (
            "moisture" in text
            or "moisture content" in text
            or "dry basis" in text
            or "wet basis" in text
            or "feedstock replacement factor" in text
        ):
            upsert_field(
                field_map,
                path="feedstock.moisture_measurement",
                value=True,
                evidence="Heuristic match: project text explicitly references moisture content or moisture-related adjustment factors.",
                extractor="feedstock_mapper",
                fill_method="heuristic",
                confidence=0.84,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))


def run_feedstock_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    if not fields:
        return {"normalized_fields": [], "raw_extraction": {"fields": []}}

    prompt = build_domain_prompt(
        domain_name="feedstock",
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
        extractor_name="feedstock_mapper",
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
