# engine/mappers/eligibility_mapper.py

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


ELIGIBILITY_PATHS = [
    "eligibility.net_negative_claim",
    "methodology.standard",
    "methodology.pathway",
    "methodology.production_subpathway",
]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_paths(EXTRACTION_FIELDS, ELIGIBILITY_PATHS)


def _instructions() -> str:
    return """
Focus on general eligibility and applicability signals.

Important interpretation rules:
- Count net-negative as supported when the project explicitly states that removals exceed emissions,
  when the climate impact is described as net negative, or when an LCA / GHG statement clearly shows
  a negative carbon footprint.
- Count methodology.standard as supported when the project explicitly names the Isometric standard.
- Count methodology.pathway as supported when the project explicitly identifies biochar as the pathway.
- Count methodology.production_subpathway only when the project clearly indicates batch / continuous
  production mode. Do not guess from generic pyrolysis wording alone.

Evidence grading:
- strong: explicit quantitative or formal statement
- moderate: clear narrative statement without full quantified support
- weak: indirect inference only

The project may be pre-operational. Do not require measured operational data for these fields.
"""


def apply_local_heuristics(
    project_context: str,
    methodology_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    project_text = (project_context or "").lower()
    methodology_text = (methodology_context or "").lower()
    combined_text = f"{project_text}\n{methodology_text}"

    field_map = {item["path"]: dict(item) for item in normalized_fields}

    # ------------------------------------------------------------------
    # eligibility.net_negative_claim
    # ------------------------------------------------------------------
    current = field_map.get("eligibility.net_negative_claim", {}).get("value")
    if current is not True:
        strong_patterns = [
            r"net[- ]negative",
            r"project removals?.{0,60}>\s*emissions?",
            r"removals?.{0,60}exceed.{0,40}emissions?",
            r"positive net removals?",
            r"net removals?.{0,40}(positive|exceed|greater than)",
            r"negative carbon footprint",
            r"net (ghg|co2e|co2eq).{0,30}(negative|below zero)",
            r"overall climate impact.{0,30}negative",
        ]
        if any(re.search(p, combined_text, re.IGNORECASE | re.DOTALL) for p in strong_patterns):
            upsert_field(
                field_map,
                path="eligibility.net_negative_claim",
                value=True,
                evidence="Heuristic match: explicit net-negative / negative-carbon-footprint evidence found in project or LCA text.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.94,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # methodology.standard
    # ------------------------------------------------------------------
    if field_map.get("methodology.standard", {}).get("value") is None:
        if "isometric" in combined_text:
            upsert_field(
                field_map,
                path="methodology.standard",
                value="Isometric",
                evidence="Heuristic match: project explicitly references the Isometric standard.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.96,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # methodology.pathway
    # ------------------------------------------------------------------
    if field_map.get("methodology.pathway", {}).get("value") is None:
        if re.search(r"\bbiochar\b", combined_text):
            upsert_field(
                field_map,
                path="methodology.pathway",
                value="biochar",
                evidence="Heuristic match: project explicitly identifies the pathway as biochar.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.96,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # methodology.production_subpathway
    # ------------------------------------------------------------------
    if field_map.get("methodology.production_subpathway", {}).get("value") is None:
        if re.search(r"\bcontinuous pyrolysis\b|\bcontinuous reactor\b|\bcontinuous operation\b", combined_text):
            upsert_field(
                field_map,
                path="methodology.production_subpathway",
                value="continuous",
                evidence="Heuristic match: project text explicitly describes continuous pyrolysis / continuous operation.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.83,
                evidence_strength="moderate",
                evidence_mode="direct",
            )
        elif re.search(r"\bbatch mode\b|\bbatch capacity\b|\brectangular kilns\b", combined_text):
            upsert_field(
                field_map,
                path="methodology.production_subpathway",
                value="batch",
                evidence="Heuristic match: project text explicitly describes batch-mode kiln operation.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.82,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))


def run_eligibility_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()

    prompt = build_domain_prompt(
        domain_name="eligibility",
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
        extractor_name="eligibility_mapper",
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
