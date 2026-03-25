# engine/mappers/storage_mapper.py

from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    normalize_domain_fields,
    parse_extraction_payload,
)


STORAGE_PREFIXES = ["storage.", "methodology.storage_pathway"]


def get_fields() -> List[Dict[str, Any]]:
    fields = []
    for f in EXTRACTION_FIELDS:
        path = f["path"]
        if path == "methodology.storage_pathway" or path.startswith("storage."):
            fields.append(f)
    return fields


def _instructions() -> str:
    return """
Focus on:
- storage pathway
- deployment methods
- stockpiling
- storage documentation
- storage environment stability
Be conservative with claims about stable storage if only future intention is described.
"""


def run_storage_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    prompt = build_domain_prompt(
        domain_name="storage",
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
        extractor_name="storage_mapper",
        fill_method="llm",
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
