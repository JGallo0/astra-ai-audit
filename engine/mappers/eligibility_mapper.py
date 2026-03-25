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
  or when the LCA / GHG statement clearly shows a negative carbon footprint or positive net removals.
- Count methodology.standard as supported when the project explicitly names the Isometric standard.
- Count methodology.pathway as supported when the project explicitly identifies biochar as the project pathway.
- Count methodology.production_subpathway only when the project clearly indicates batch / continuous /
  distributed / centralized production mode. Do not guess from generic pyrolysis wording alone.

Evidence grading:
- strong: explicit quantitative or formal methodological statement (e.g. "net negative", "-2,720.97 kgCO2eq.",
  "Isometric", "biochar pathway")
- moderate: clear narrative statement without quantified support
- weak: indirect inference only

Be conservative:
- The project is pre-operational, so do not invent measured operational evidence.
- Prefer null over false when eligibility wording is incomplete or only implied.
"""


def _set_if_missing(
    field_map: Dict[str, Dict[str, Any]],
    path: str,
    value: Any,
    evidence: str,
    confidence: float,
    evidence_strength: str,
    evidence_mode: str,
) -> None:
    if field_map.get(path, {}).get("value") is None:
        upsert_field(
            field_map,
            path=path,
            value=value,
            evidence=evidence,
            extractor="eligibility_mapper",
            fill_method="heuristic",
            confidence=confidence,
            evidence_strength=evidence_strength,
            evidence_mode=evidence_mode,
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

    # ------------------------------------------------------------------
    # eligibility.net_negative_claim
    # ------------------------------------------------------------------
    current = field_map.get("eligibility.net_negative_claim", {}).get("value")
    if current is not True:
        strong_patterns = [
            r"net[- ]negative",
            r"project removals?.{0,40}>\s*emissions?",
            r"removals?.{0,40}exceed.{0,25}emissions?",
            r"positive net removals?",
            r"negative carbon footprint",
            r"-\s*2[,\.]?[0-9]{3}",  # catches values like -2720.97 / -2,720.97
            r"kgco2eq",
            r"tco2e\/t",
        ]
        if any(re.search(p, combined_text, re.IGNORECASE | re.DOTALL) for p in strong_patterns):
            upsert_field(
                field_map,
                path="eligibility.net_negative_claim",
                value=True,
                evidence="Heuristic match: explicit net-negative / negative-carbon-footprint evidence found in project or LCA text.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # methodology.standard
    # ------------------------------------------------------------------
    _set_if_missing(
        field_map=field_map,
        path="methodology.standard",
        value="Isometric" if "isometric" in combined_text else None,
        evidence="Heuristic match: project explicitly references the Isometric standard."
        if "isometric" in combined_text else "",
        confidence=0.95,
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
                confidence=0.95,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # methodology.production_subpathway
    # ------------------------------------------------------------------
    if field_map.get("methodology.production_subpathway", {}).get("value") is None:
        # conservative: only fill when clear wording exists
        if re.search(r"\bcontinuous pyrolysis\b|\bcontinuous reactor\b|\bcontinuous operation\b", combined_text):
            upsert_field(
                field_map,
                path="methodology.production_subpathway",
                value="continuous",
                evidence="Heuristic match: project text explicitly describes continuous pyrolysis / continuous operation.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.82,
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
                confidence=0.80,
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
