# engine/mappers/feedstock_mapper.py

from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    normalize_domain_fields,
    parse_extraction_payload,
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
Be conservative.
For feedstock.source_locations:
- extract only explicit biomass sourcing places (city/municipality/state/region/site)
- return list_string values exactly grounded in the text
- do not infer locations from company headquarters or generic country mentions
"""


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

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
