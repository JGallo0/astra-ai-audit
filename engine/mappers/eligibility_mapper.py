# engine/mappers/eligibility_mapper.py

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


ELIGIBILITY_PATHS = [
    "eligibility.net_negative_claim",
    "methodology.standard",
    "methodology.pathway",
    "methodology.production_subpathway",
]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_paths(EXTRACTION_FIELDS, ELIGIBILITY_PATHS)


def _instructions() -> str:
    return """
Focus on general eligibility and applicability signals.

Strong signals:
- "net negative", "net removals exceed emissions", "positive net removals"
- explicit identification of Isometric and biochar pathway
- explicit statement of production subpathway
"""


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    if field_map.get("eligibility.net_negative_claim", {}).get("value") is not True:
        patterns = [
            r"net[- ]?negative",
            r"net removals?",
            r"positive net removals?",
            r"removals?.{0,40}exceed.{0,20}emissions?",
            r"after deducting all process emissions",
            r"tco2e per tonne of biochar",
        ]
        if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in patterns):
            upsert_field(
                field_map,
                path="eligibility.net_negative_claim",
                value=True,
                evidence="Heuristic match: project text indicates net-negative removals or positive net removals.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.88,
                evidence_strength="strong",
                evidence_mode="inferred",
            )

    return merge_normalized_fields(list(field_map.values()))


def run_eligibility_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    prompt = build_domain_prompt(
        domain_name="eligibility",
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
        extractor_name="eligibility_mapper",
        fill_method="llm",
    )
    normalized = apply_local_heuristics(project_context, normalized)

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
