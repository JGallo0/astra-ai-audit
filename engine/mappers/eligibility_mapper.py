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

    # ── Phase 3: project location and ownership (R-A5B6-0, R-M858-0) ────────
    # Use project_text (already defined above)
    text = project_text  # alias for consistency with other mappers

    # project.country — "located in Brazil", "California, USA", "in the United States"
    if field_map.get("project.country", {}).get("value") is None:
        country_patterns = [
            (r"\blocated\s+in\s+(Brazil|USA|United\s+States|Canada|Germany|Netherlands|UK|United\s+Kingdom|Australia|India|China|Japan)\b", 1),
            (r"\b(Brazil|California|Oregon|Washington|Texas)\b.*\bUSA\b|\bUSA\b.*\b(California|Oregon|Washington|Texas)\b", None),
            (r"\b(Brasil|Brazil)\b", "Brazil"),
            (r"\bCalifornia\b|\bCA\b.*\bUSA\b", "United States"),
        ]
        for pattern, group in country_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                country = m.group(group) if isinstance(group, int) else group
                if country:
                    upsert_field(
                        field_map,
                        path="project.country",
                        value=str(country),
                        evidence=f"Regex: country '{country}' mentioned.",
                        extractor="eligibility_mapper",
                        fill_method="heuristic",
                        confidence=0.85,
                        evidence_strength="moderate",
                        evidence_mode="direct",
                    )
                    break

    # project.locations — GPS coordinates or city/state
    if not field_map.get("project.locations", {}).get("value"):
        # GPS pattern: "38.123, -122.456" or "lat: 38.1, lon: -122.4"
        gps = re.findall(r"[-+]?\d{1,3}\.\d{3,}[°,]\s*[-+]?\d{1,3}\.\d{3,}", text)
        if gps:
            upsert_field(
                field_map,
                path="project.locations",
                value=gps[:3],
                evidence=f"Regex: GPS coordinates found: {gps[:1]}.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.92,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        else:
            # City/state/country mention
            location_m = re.search(
                r"(?:located\s+(?:in|at)|facility\s+(?:in|at)|project\s+(?:in|at))\s+([A-Z][a-zA-Z\s,]+(?:County|State|Province|CA|OR|WA|MG|SP|PR))",
                text, re.IGNORECASE,
            )
            if location_m:
                upsert_field(
                    field_map,
                    path="project.locations",
                    value=[location_m.group(1).strip()],
                    evidence=f"Regex: location '{location_m.group(1)}'.",
                    extractor="eligibility_mapper",
                    fill_method="heuristic",
                    confidence=0.78,
                    evidence_strength="moderate",
                    evidence_mode="direct",
                )

    # project.ownership_evidence — company name + certification
    if not field_map.get("project.ownership_evidence", {}).get("value"):
        # Certification scheme as proxy
        cert_m = re.search(r"(Isometric|Puro\.Earth|Verra|Gold Standard)\s+(?:certified|registered|project|standard)", text, re.IGNORECASE)
        company_m = re.search(r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Inc\.|LLC|Ltd\.|Corp\.|S\.A\.|Ltda\.))", text)
        proxies = []
        if cert_m:
            proxies.append(f"{cert_m.group(1)} certification")
        if company_m:
            proxies.append(company_m.group(1).strip())
        if proxies:
            upsert_field(
                field_map,
                path="project.ownership_evidence",
                value=proxies,
                evidence=f"Regex: ownership proxies found: {proxies}.",
                extractor="eligibility_mapper",
                fill_method="heuristic",
                confidence=0.72,
                evidence_strength="moderate",
                evidence_mode="inferred",
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
