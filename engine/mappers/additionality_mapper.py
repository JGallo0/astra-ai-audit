# engine/mappers/additionality_mapper.py

from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_paths,
    normalize_domain_fields,
    parse_extraction_payload,
)


ADDITIONALITY_PATHS = [
    "eligibility.additionality_claim",
]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_paths(EXTRACTION_FIELDS, ADDITIONALITY_PATHS)


def _instructions() -> str:
    return """
Focus only on additionality.

Count as strong signals only when the project explicitly claims or explains:
- financial additionality
- regulatory additionality
- environmental additionality
- counterfactual / baseline rationale
Do not convert vague sustainability language into additionality.
"""


def run_additionality_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    prompt = build_domain_prompt(
        domain_name="additionality",
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
        extractor_name="additionality_mapper",
        fill_method="llm",
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
