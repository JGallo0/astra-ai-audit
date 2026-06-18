# engine/mappers/storage_mapper.py

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


STORAGE_PREFIXES = ["storage.", "methodology.storage_pathway"]


def get_fields() -> List[Dict[str, Any]]:
    return [
        f for f in EXTRACTION_FIELDS
        if f["path"] == "methodology.storage_pathway" or f["path"].startswith("storage.")
    ]


def _instructions() -> str:
    return """
Focus on:
- storage pathway
- soil deployment methods
- storage documentation
- storage environment stability

STRICT RULES:
- deployment_methods MUST describe actual application/use in soil
- DO NOT include:
  - engineering terms
  - sampling plans
  - maintenance plans
  - diagrams
  - generic phrases

Valid examples:
- soil application
- land application
- field incorporation
- soil blending
- agronomic application

Prefer null over incorrect values.
"""


# ------------------------------------------------------------
# SANITIZATION
# ------------------------------------------------------------
def sanitize_storage_fields(
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    deployment = field_map.get("storage.soil.deployment_methods", {}).get("value")

    if isinstance(deployment, list):
        cleaned = []

        for item in deployment:
            text = str(item).lower()

            # BLOQUEIO de termos inválidos
            if any(bad in text for bad in [
                "diagram",
                "sampling",
                "maintenance",
                "plan",
                "reactor",
            ]):
                continue

            cleaned.append(item)

        if cleaned:
            field_map["storage.soil.deployment_methods"]["value"] = cleaned
        else:
            field_map.pop("storage.soil.deployment_methods", None)

    return list(field_map.values())


# ------------------------------------------------------------
# HEURISTICS
# ------------------------------------------------------------
def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = (project_context or "").lower()
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    current = field_map.get("storage.soil.deployment_methods", {}).get("value")

    if current in (None, "", [], False):
        if any(term in text for term in [
            "soil application",
            "applied to soil",
            "land application",
            "field application",
            "agricultural use",
        ]):
            upsert_field(
                field_map,
                path="storage.soil.deployment_methods",
                value=["soil application"],
                evidence="Heuristic match: project describes application of biochar to soil.",
                extractor="storage_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ── Phase 3: soil temperature (R-F5RZ-0) ────────────────────────────────

    # Annual average soil temperature: "18.5°C", "mean soil temperature of 20°C"
    if field_map.get("storage.soil.annual_avg_temp_celsius", {}).get("value") is None:
        m = re.search(
            r"(?:annual\s+average\s+|mean\s+|average\s+)?soil\s+temperature\s+(?:of\s+|=\s*|:\s*)?(\d+\.?\d*)\s*°?C",
            text, re.IGNORECASE,
        )
        if not m:
            m = re.search(
                r"Tsoil\s*[=:]\s*(\d+\.?\d*)",
                text, re.IGNORECASE,
            )
        if m:
            upsert_field(
                field_map,
                path="storage.soil.annual_avg_temp_celsius",
                value=float(m.group(1)),
                evidence=f"Regex: soil temperature = {m.group(1)}°C.",
                extractor="storage_mapper",
                fill_method="heuristic",
                confidence=0.88,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # Temperature method: direct measurement vs global database
    if field_map.get("storage.soil.temperature_method", {}).get("value") is None:
        if re.search(r"Lembrechts|global\s+(?:soil\s+temperature\s+)?database", text, re.IGNORECASE):
            upsert_field(
                field_map,
                path="storage.soil.temperature_method",
                value="lembrechts_2022",
                evidence="Regex: reference to Lembrechts et al. or global database.",
                extractor="storage_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif re.search(r"soil\s+temperature\s+(?:measurement|sensor|monitoring|measured)", text, re.IGNORECASE):
            upsert_field(
                field_map,
                path="storage.soil.temperature_method",
                value="direct_measurement",
                evidence="Regex: direct soil temperature measurement mentioned.",
                extractor="storage_mapper",
                fill_method="heuristic",
                confidence=0.80,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def run_storage_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()

    prompt = build_domain_prompt(
        domain_name="storage",
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
        extractor_name="storage_mapper",
        fill_method="llm",
    )

    # 🔥 NOVO
    normalized = sanitize_storage_fields(normalized)

    # 🔥 NOVO
    normalized = apply_local_heuristics(
        project_context=project_context,
        normalized_fields=normalized,
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
