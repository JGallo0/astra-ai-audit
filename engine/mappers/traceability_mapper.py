# engine/mappers/traceability_mapper.py

from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    normalize_domain_fields,
    parse_extraction_payload,
)


TRACEABILITY_PREFIXES = ["traceability."]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_prefixes(EXTRACTION_FIELDS, TRACEABILITY_PREFIXES)


def _instructions() -> str:
    return """
Focus on traceability and chain of custody:
- chain of custody
- logs
- batch IDs
- transport records
- documentation trail
Strong signals include:
chain of custody, delivery note, lot ID, archived records, tracking sheet, dispatch record.
"""


def run_traceability_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    prompt = build_domain_prompt(
        domain_name="traceability",
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
        extractor_name="traceability_mapper",
        fill_method="llm",
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
