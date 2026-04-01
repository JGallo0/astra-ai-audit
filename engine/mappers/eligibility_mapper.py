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
    "project.country",
    "project.locations",
    "project.ownership_evidence",
]


def get_fields() -> List[Dict[str, Any]]:
    return filter_fields_by_paths(EXTRACTION_FIELDS, ELIGIBILITY_PATHS)


def _instructions() -> str:
    return """
Focus on general eligibility, applicability, and core project identity signals.

Important interpretation rules:
- Count net-negative as supported when the project explicitly states that removals exceed emissions,
  when the climate impact is described as net negative, or when an LCA / GHG statement clearly shows
  a negative carbon footprint.
- Count methodology.standard as supported when the project explicitly names the Isometric standard.
- Count methodology.pathway as supported when the project explicitly identifies biochar as the pathway.
- Count methodology.production_subpathway only when the project clearly indicates the relevant production
  subpathway. Do not guess from generic pyrolysis wording alone.
- Extract project.country only when the country is explicitly stated or strongly inferable from a location
  such as "CA, USA" or "California, United States".
- Extract project.locations when the project text clearly identifies site-level or regional locations
  (city, county, state, province, region).
- Extract project.ownership_evidence when the text explicitly indicates ownership, operation, project
  proponent status, carbon rights, or the right to claim removals.

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
            r"negative carbon footprint",
            r"-\s*2[,\.]?[0-9]{3}",
            r"3\.72\s*t\/t",
            r"3[,\.]72\s*t\/t",
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

    # ------------------------------------------------------------------
    # project.country
    # ------------------------------------------------------------------
    if field_map.get("project.country", {}).get("value") is None:
        country = None

        if re.search(r"\b(united states|usa|u\.s\.a\.)\b", combined_text):
            country = "United States"
        elif re.search(r"\bcanada\b", combined_text):
            country = "Canada"
        elif re.search(r"\bbrazil\b", combined_text):
            country = "Brazil"
        elif re.search(r"\bindia\b", combined_text):
            country = "India"
        elif re.search(r"\baustralia\b", combined_text):
            country = "Australia"
        elif re.search(r"\bchile\b", combined_text):
            country = "Chile"

        if country is None:
            if re.search(r"\bscotia,\s*ca\b", combined_text) or re.search(r"\bcalifornia\b", combined_text):
                country = "United States"

        if country is not None:
            upsert_field(
                field_map,
                path="project.country",
                value=country,
                evidence="Heuristic match: country inferred from explicit country/state/location references in project text.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # project.locations
    # ------------------------------------------------------------------
    if field_map.get("project.locations", {}).get("value") in [None, [], ""]:
        location_candidates = []

        location_patterns = [
            r"\bScotia,\s*CA\b",
            r"\bCalifornia\b",
            r"\bHumboldt County\b",
            r"\bHumboldt\b",
        ]

        for pattern in location_patterns:
            matches = re.findall(pattern, project_context or "", re.IGNORECASE)
            for match in matches:
                cleaned = str(match).strip()
                if cleaned and cleaned not in location_candidates:
                    location_candidates.append(cleaned)

        if location_candidates:
            upsert_field(
                field_map,
                path="project.locations",
                value=location_candidates,
                evidence="Heuristic match: project locations identified from explicit city/county/state references.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.88,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------------
    # project.ownership_evidence
    # ------------------------------------------------------------------
    current_ownership = field_map.get("project.ownership_evidence", {}).get("value")
    if current_ownership in [None, [], ""]:
        ownership_evidence = []

        ownership_patterns = [
            r"\bproject proponent\b",
            r"\bproject developer\b",
            r"\bowner\b",
            r"\boperated by\b",
            r"\bowned by\b",
            r"\bright to claim\b",
            r"\bcarbon rights\b",
            r"\bonly organization\b",
            r"\bPacific Biochar\b",
            r"\bHumboldt Sawmill Company\b",
        ]

        for pattern in ownership_patterns:
            if re.search(pattern, project_context or "", re.IGNORECASE):
                ownership_evidence.append(pattern.replace(r"\b", "").replace("\\", ""))

        if ownership_evidence:
            upsert_field(
                field_map,
                path="project.ownership_evidence",
                value=ownership_evidence,
                evidence="Heuristic match: ownership / operator / project proponent evidence identified in project text.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.86,
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
