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
            "biochar application",
            "direct application",
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

    # ------------------------------------------------------------
    # storage.storage_module
    # ------------------------------------------------------------
    
    current_module = field_map.get("storage.storage_module", {}).get("value")
    storage_pathway = field_map.get("methodology.storage_pathway", {}).get("value")
    deployment_methods = field_map.get("storage.soil.deployment_methods", {}).get("value")

    if current_module in (None, "", [], False):
        if (
            str(storage_pathway).strip().lower() == "soil"
            or (isinstance(deployment_methods, list) and len(deployment_methods) > 0)
            or any(term in text for term in [
                "soil application",
                "land application",
                "field application",
                "biochar application",
                "direct application",
                "soil environments",
            ])
        ):
            upsert_field(
                field_map,
                path="storage.storage_module",
                value="Biochar Storage in Soil Environments",
                evidence="Heuristic match: soil storage pathway and/or soil deployment language indicates the Isometric soil storage module.",
                extractor="storage_mapper",
                fill_method="heuristic",
                confidence=0.92,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # storage.storage_location
    # ------------------------------------------------------------
    
    current_location = field_map.get("storage.storage_location", {}).get("value")

    if current_location in (None, "", [], False):
        location_candidates = []

        location_patterns = [
            r"\bScotia,\s*CA\b",
            r"\bHumboldt County\b",
            r"\bCalifornia\b",
            r"\bMendocino County\b",
            r"\bSonoma County\b",
            r"\bSanta Cruz County\b",
            r"\bMonterey County\b",
            r"\bDel Norte County\b",
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
                path="storage.storage_location",
                value=location_candidates[0],
                evidence="Heuristic match: storage/application location identified from explicit project geography references.",
                extractor="storage_mapper",
                fill_method="heuristic",
                confidence=0.85,
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
