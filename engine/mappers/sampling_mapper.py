# engine/mappers/sampling_mapper.py

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


SAMPLING_PREFIXES = ["sampling."]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_prefixes(EXTRACTION_FIELDS, SAMPLING_PREFIXES)


def _instructions() -> str:
    return """
Focus on:
- sampling method A/B
- batch definition
- sampling plan
- frequency per batch / per lot
Strong signals include:
"24-hour production window", "per production batch", "composite samples",
"sampling protocol", "sampling plan", "method A", "method B".
"""


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    if field_map.get("sampling.batch_definition_days", {}).get("value") is None:
        hour_match = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?\s*hour production window", text)
        if hour_match:
            hours = float(hour_match.group(1))
            days = max(1, int(round(hours / 24.0)))
            upsert_field(
                field_map,
                path="sampling.batch_definition_days",
                value=days,
                evidence=f"Heuristic match: {hour_match.group(1)}-hour production window.",
                extractor="sampling_mapper",
                fill_method="heuristic",
                confidence=0.92,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        else:
            day_match = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?\s*day production window", text)
            if day_match:
                days = max(1, int(round(float(day_match.group(1)))))
                upsert_field(
                    field_map,
                    path="sampling.batch_definition_days",
                    value=days,
                    evidence=f"Heuristic match: {day_match.group(1)}-day production window.",
                    extractor="sampling_mapper",
                    fill_method="heuristic",
                    confidence=0.92,
                    evidence_strength="strong",
                    evidence_mode="direct",
                )

    if field_map.get("sampling.sampling_plan_defined", {}).get("value") is not True:
        if re.search(r"(once per production batch)|(per batch sampling)|(batch sampling)|(per lot sampling)|(composite samples?.{0,40}per)|(sampling plan)|(sampling protocol)", text, re.DOTALL):
            upsert_field(
                field_map,
                path="sampling.sampling_plan_defined",
                value=True,
                evidence="Heuristic match: batch- or lot-based sampling procedure identified.",
                extractor="sampling_mapper",
                fill_method="heuristic",
                confidence=0.89,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))


def run_sampling_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    prompt = build_domain_prompt(
        domain_name="sampling",
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
        extractor_name="sampling_mapper",
        fill_method="llm",
    )
    normalized = apply_local_heuristics(project_context, normalized)

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
