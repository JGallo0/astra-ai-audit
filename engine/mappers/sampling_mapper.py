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
Focus on sampling evidence:
- batch definition
- sampling plan
- frequency per batch / per lot / regular interval
- method A/B only when explicitly stated
- laboratory-linked sampling procedures

Important interpretation rules:
- Count sampling.sampling_plan_defined when the project explicitly describes regular analysis,
  analytical procedures, sampling frequency in an annex, per-batch records, archived samples,
  or batch-level laboratory monitoring.
- Count sampling.batch_definition_days when the text explicitly states a 24-hour production window,
  or when continuous 24 h/day operation is clearly used as the practical batch window in the project context.
- Do not guess sampling.method A/B unless the project explicitly names a method.

Evidence grading:
- strong: "per batch", "batch-level", "sampling plan", "sampling frequency", "archived samples"
- moderate: recurring lab analysis and annexed analytical procedures
- weak: generic mention of quality analysis only
"""


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    # ------------------------------------------------------------------
    # sampling.batch_definition_days
    # ------------------------------------------------------------------
    current = field_map.get("sampling.batch_definition_days", {}).get("value")
    if current is None:
        hour_match = re.search(
            r"(\d+(?:\.\d+)?)\s*[- ]?\s*hour production window",
            text,
            re.IGNORECASE,
        )
        if hour_match:
            hours = float(hour_match.group(1))
            days = max(1, int(round(hours / 24.0)))
            upsert_field(
                field_map,
                path="sampling.batch_definition_days",
                value=days,
                evidence=f"Heuristic match: explicit {hour_match.group(1)}-hour production window found.",
                extractor="sampling_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif re.search(r"\b24\s*h\/day\b|\b24\s*hours?\/day\b|\bcontinuous\s*\(24 h\/day", text, re.IGNORECASE):
            upsert_field(
                field_map,
                path="sampling.batch_definition_days",
                value=1,
                evidence="Heuristic match: project describes continuous 24 h/day operation, used conservatively as a 1-day batch window.",
                extractor="sampling_mapper",
                fill_method="heuristic",
                confidence=0.72,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )

    # ------------------------------------------------------------------
    # sampling.sampling_plan_defined
    # ------------------------------------------------------------------
    current = field_map.get("sampling.sampling_plan_defined", {}).get("value")
    if current is not True:
        strong_patterns = [
            r"sampling plan",
            r"sampling frequency",
            r"per production batch",
            r"batch-level",
            r"per batch",
            r"samples are archived",
            r"biochar samples are archived",
            r"analytical procedures and sampling frequency are included",
        ]
        moderate_patterns = [
            r"regularly analyzed",
            r"laboratory analysis",
            r"sample monitoring",
            r"records are archived",
            r"per batch",
            r"operational and laboratory data are collected per batch",
        ]

        if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in strong_patterns):
            upsert_field(
                field_map,
                path="sampling.sampling_plan_defined",
                value=True,
                evidence="Heuristic match: explicit sampling-plan / frequency / batch-level wording found.",
                extractor="sampling_mapper",
                fill_method="heuristic",
                confidence=0.91,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif sum(bool(re.search(p, text, re.IGNORECASE | re.DOTALL)) for p in moderate_patterns) >= 2:
            upsert_field(
                field_map,
                path="sampling.sampling_plan_defined",
                value=True,
                evidence="Heuristic match: recurring laboratory analysis plus batch/archiving language implies a defined sampling plan.",
                extractor="sampling_mapper",
                fill_method="heuristic",
                confidence=0.78,
                evidence_strength="moderate",
                evidence_mode="inferred",
            )

    # ------------------------------------------------------------------
    # sampling.method
    # ------------------------------------------------------------------
    current = field_map.get("sampling.method", {}).get("value")
    if current is None:
        if re.search(r"\bmethod a\b", text, re.IGNORECASE):
            upsert_field(
                field_map,
                path="sampling.method",
                value="A",
                evidence="Heuristic match: explicit reference to Method A.",
                extractor="sampling_mapper",
                fill_method="heuristic",
                confidence=0.88,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif re.search(r"\bmethod b\b", text, re.IGNORECASE):
            upsert_field(
                field_map,
                path="sampling.method",
                value="B",
                evidence="Heuristic match: explicit reference to Method B.",
                extractor="sampling_mapper",
                fill_method="heuristic",
                confidence=0.88,
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

    normalized = apply_local_heuristics(
        project_context=project_context,
        normalized_fields=normalized,
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
