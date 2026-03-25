# engine/mappers/durability_mapper.py

import re
from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_paths,
    merge_normalized_fields,
    normalize_domain_fields,
    parse_extraction_payload,
    upsert_field,
)


DURABILITY_PATHS = [
    "eligibility.durability_years",
    "methodology.durability_option",
]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_paths(EXTRACTION_FIELDS, DURABILITY_PATHS)


def _instructions() -> str:
    return """
Focus on durability, permanence, and declared durability option.

Strong signals:
- explicit durability year values such as 200 or 1000
- "chosen 200 years", "durability option"
- references to permanence / stable storage conditions
"""


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    if field_map.get("eligibility.durability_years", {}).get("value") is None:
        if re.search(r"\b1000\s+years?\b", text):
            upsert_field(
                field_map,
                path="eligibility.durability_years",
                value=1000,
                evidence="Heuristic match: 1000 years mentioned in project evidence.",
                extractor="durability_mapper",
                fill_method="heuristic",
                confidence=0.86,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif re.search(r"\b200\s+years?\b", text):
            upsert_field(
                field_map,
                path="eligibility.durability_years",
                value=200,
                evidence="Heuristic match: 200 years mentioned in project evidence.",
                extractor="durability_mapper",
                fill_method="heuristic",
                confidence=0.84,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    if field_map.get("methodology.durability_option", {}).get("value") is None:
        if re.search(r"combined[_ -]?200[_ -]?1000|combined 200 1000", text):
            upsert_field(
                field_map,
                path="methodology.durability_option",
                value="combined_200_1000",
                evidence="Heuristic match: combined 200/1000 durability option referenced.",
                extractor="durability_mapper",
                fill_method="heuristic",
                confidence=0.83,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )
        elif re.search(r"\b1000\b", text):
            upsert_field(
                field_map,
                path="methodology.durability_option",
                value="1000",
                evidence="Heuristic match: 1000 durability option referenced.",
                extractor="durability_mapper",
                fill_method="heuristic",
                confidence=0.82,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )
        elif re.search(r"\b200\b", text):
            upsert_field(
                field_map,
                path="methodology.durability_option",
                value="200",
                evidence="Heuristic match: 200 durability option referenced.",
                extractor="durability_mapper",
                fill_method="heuristic",
                confidence=0.82,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )

    return merge_normalized_fields(list(field_map.values()))


def run_durability_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    prompt = build_domain_prompt(
        domain_name="durability",
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
        extractor_name="durability_mapper",
        fill_method="llm",
    )
    normalized = apply_local_heuristics(project_context, normalized)

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
