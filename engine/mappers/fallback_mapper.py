# engine/mappers/fallback_mapper.py

from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_paths,
    normalize_domain_fields,
    parse_extraction_payload,
)


def get_fields_for_missing(missing_paths: List[str]) -> List[Dict[str, Any]]:
    return filter_fields_by_paths(EXTRACTION_FIELDS, missing_paths)


def _instructions() -> str:
    return """
This is the fallback extractor.
Only fill fields when evidence is reasonably clear.
Be conservative.
Do not guess.
Prefer null when uncertain.

PROJECT-SPECIFIC GUIDANCE (critical):
- project.country:
  Fill only when a country is explicitly named as the project location.
  Do not infer from organization nationality, language, or methodology origin.
- project.locations:
  Fill with explicit site/location names (city, state, municipality, region, facility names).
  Return a list_string with only locations evidenced in the text.
  Do not include generic terms like "project area" without a named place.
- project.ownership_evidence:
  Fill with explicit ownership/control evidence references (e.g., land title, concession,
  lease agreement, supply contract, operator authorization, right-to-operate statement).
  Return a list_string of evidence labels found in source text; do not invent document names.
"""


def run_fallback_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
    missing_paths: List[str],
) -> Dict[str, Any]:
    if not missing_paths:
        return {"normalized_fields": [], "raw_extraction": {"fields": []}}

    fields = get_fields_for_missing(missing_paths)

    prompt = build_domain_prompt(
        domain_name="fallback",
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
        extractor_name="fallback_mapper",
        fill_method="fallback",
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
