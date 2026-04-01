# engine/mappers/traceability_mapper.py

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
chain of custody, delivery note, lot ID, archived records, tracking sheet, dispatch record,
sourcing records, feedstock-to-product traceability, named suppliers or sawmills, and documented
input-to-output tracking.

Equivalent documentary evidence may count even when no formal diagram is shown.
"""


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    # ------------------------------------------------------------
    # traceability.chain_of_custody_diagram
    # ------------------------------------------------------------
    current = field_map.get("traceability.chain_of_custody_diagram", {}).get("value")

    if current in (None, "", [], False):
        strong_patterns = [
            r"chain of custody",
            r"tracking",
            r"traceability",
            r"delivery records",
            r"dispatch records",
            r"sourcing records",
            r"lot id",
            r"batch id",
            r"archived records",
            r"feedstock-to-product",
            r"feedstock to product",
            r"from individual sawmills",
            r"individual sawmills",
            r"humboldt sawmill company",
        ]

        matched_terms = []
        for pattern in strong_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matched_terms.append(pattern)

        if matched_terms:
            upsert_field(
                field_map,
                path="traceability.chain_of_custody_diagram",
                value=True,
                evidence="Heuristic match: chain-of-custody or equivalent documentary traceability evidence identified in project text.",
                extractor="traceability_mapper",
                fill_method="heuristic",
                confidence=0.86,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))


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

    normalized = apply_local_heuristics(
        project_context=project_context,
        normalized_fields=normalized,
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
