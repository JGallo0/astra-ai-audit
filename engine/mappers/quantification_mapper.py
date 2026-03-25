# engine/mappers/quantification_mapper.py

from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    normalize_domain_fields,
    parse_extraction_payload,
)


QUANTIFICATION_PREFIXES = ["quantification.", "biochar.characterization.", "product.", "legal."]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_prefixes(EXTRACTION_FIELDS, QUANTIFICATION_PREFIXES)


def _instructions() -> str:
    return """
Focus on quantification-related evidence:
- boundaries
- uncertainty
- LCA references
- measurement completeness
- biochar characterization
- product standard compliance
- legal measurement requirements
Strong signals include:
LCA, uncertainty analysis, ISO/IEC 17025, lab reports, measurement tables, standard compliance.
"""


def run_quantification_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    prompt = build_domain_prompt(
        domain_name="quantification",
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
        extractor_name="quantification_mapper",
        fill_method="llm",
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
