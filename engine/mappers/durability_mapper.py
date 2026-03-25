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


DURABILITY_PATHS = [
    "eligibility.durability_years",
    "methodology.durability_option",
]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_paths(EXTRACTION_FIELDS, DURABILITY_PATHS)


def _instructions() -> str:
    return """
Focus only on durability and declared durability option.

Important interpretation rules:
- Count methodology.durability_option when the project explicitly states the durability
  classification/pathway/threshold selected under Isometric.
- Count eligibility.durability_years when the project explicitly references a +200-year or
  +1000-year durability pathway/classification/threshold.
- Use only these allowed durability_option values when supported:
  "200", "1000", "combined_200_1000"
- Do not require operational data; narrative and methodological statements are acceptable here
  if they are explicit.
- Prefer null over false if the evidence is unclear.

Strong signals:
- "+200-year durability classification"
- "+200-year durability pathway"
- "The project applies the +200-year durability classification under the Isometric protocol"
- "Fully support the +200-year durability pathway"
- equivalent wording for +1000-year or combined 200/1000
"""


def _set_durability_200(field_map: Dict[str, Dict[str, Any]]) -> None:
    upsert_field(
        field_map,
        path="methodology.durability_option",
        value="200",
        evidence="Heuristic match: explicit +200-year durability classification/pathway wording found.",
        extractor="durability_mapper",
        fill_method="heuristic",
        confidence=0.97,
        evidence_strength="strong",
        evidence_mode="direct",
    )

    upsert_field(
        field_map,
        path="eligibility.durability_years",
        value=200,
        evidence="Heuristic match: explicit +200-year durability classification/pathway wording found.",
        extractor="durability_mapper",
        fill_method="heuristic",
        confidence=0.97,
        evidence_strength="strong",
        evidence_mode="direct",
    )


def _set_durability_1000(field_map: Dict[str, Dict[str, Any]]) -> None:
    upsert_field(
        field_map,
        path="methodology.durability_option",
        value="1000",
        evidence="Heuristic match: explicit +1000-year durability classification/pathway wording found.",
        extractor="durability_mapper",
        fill_method="heuristic",
        confidence=0.97,
        evidence_strength="strong",
        evidence_mode="direct",
    )

    upsert_field(
        field_map,
        path="eligibility.durability_years",
        value=1000,
        evidence="Heuristic match: explicit +1000-year durability classification/pathway wording found.",
        extractor="durability_mapper",
        fill_method="heuristic",
        confidence=0.97,
        evidence_strength="strong",
        evidence_mode="direct",
    )


def apply_local_heuristics(
    project_context: str,
    methodology_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    project_text = (project_context or "").lower()
    methodology_text = (methodology_context or "").lower()
    combined_text = f"{project_text}\n{methodology_text}"

    field_map = {item["path"]: dict(item) for item in normalized_fields}

    combined_200_1000_patterns = [
        r"combined[_ -]?200[_ -]?1000",
        r"combined 200 1000",
        r"200/1000",
        r"200-year and 1000-year",
    ]
    durability_1000_patterns = [
        r"\+?\s*1000[- ]year durability",
        r"1000[- ]year durability pathway",
        r"1000[- ]year durability classification",
        r"durability threshold.{0,20}1000",
        r"at least 1000 years",
    ]
    durability_200_patterns = [
        r"\+?\s*200[- ]year durability",
        r"200[- ]year durability pathway",
        r"200[- ]year durability classification",
        r"durability threshold.{0,20}200",
        r"fully support the \+?200[- ]year durability pathway",
        r"applies the \+?200[- ]year durability classification",
        r"targets the \+?200[- ]year durability class",
    ]

    if any(re.search(p, combined_text, re.IGNORECASE | re.DOTALL) for p in combined_200_1000_patterns):
        upsert_field(
            field_map,
            path="methodology.durability_option",
            value="combined_200_1000",
            evidence="Heuristic match: explicit combined 200/1000 durability wording found.",
            extractor="durability_mapper",
            fill_method="heuristic",
            confidence=0.96,
            evidence_strength="strong",
            evidence_mode="direct",
        )
    elif any(re.search(p, combined_text, re.IGNORECASE | re.DOTALL) for p in durability_1000_patterns):
        _set_durability_1000(field_map)
    elif any(re.search(p, combined_text, re.IGNORECASE | re.DOTALL) for p in durability_200_patterns):
        _set_durability_200(field_map)

    return merge_normalized_fields(list(field_map.values()))


def run_durability_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()

    prompt = build_domain_prompt(
        domain_name="durability",
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
        extractor_name="durability_mapper",
        fill_method="llm",
    )

    normalized = apply_local_heuristics(
        project_context=project_context,
        methodology_context=methodology_context,
        normalized_fields=normalized,
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
