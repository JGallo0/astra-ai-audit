import re
from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    filter_fields_by_paths,
    merge_normalized_fields,
    normalize_domain_fields,
    parse_extraction_payload,
    upsert_field,
)


MANAGEMENT_PREFIXES = [
    "management.",
]

MANAGEMENT_EXTRA_PATHS = [
    "management.adaptive_management_plan",
    "management.information_sharing_plan",
    "management.emergency_response_plan",
    "management.pause_or_stop_conditions",
    "management.monitoring_triggers",
]


def get_fields() -> List[Dict[str, Any]]:
    prefixed = filter_fields_by_prefixes(EXTRACTION_FIELDS, MANAGEMENT_PREFIXES)
    extra = filter_fields_by_paths(EXTRACTION_FIELDS, MANAGEMENT_EXTRA_PATHS)

    merged = {f["path"]: f for f in prefixed}
    for f in extra:
        merged[f["path"]] = f

    return list(merged.values())


def _instructions() -> str:
    return """
Focus on adaptive management and operational response planning.

Important interpretation rules:
- Count management.adaptive_management_plan when the project explicitly describes
  an adaptive management framework or equivalent approach for revising operations.
- Count management.information_sharing_plan when the project explicitly describes
  information sharing, communication channels, internal reporting, or escalation of incidents/findings.
- Count management.emergency_response_plan when the project explicitly describes
  emergency response procedures, incident response, contingency actions, or equivalent.
- Count management.pause_or_stop_conditions when the project explicitly states conditions
  under which operations may be paused, stopped, or suspended.
- Count management.monitoring_triggers when the project explicitly states thresholds, triggers,
  exceedances, review points, or conditions that trigger corrective review/action.
- Prefer null over false when unclear.
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

    # ------------------------------------------------------------
    # management.adaptive_management_plan
    # ------------------------------------------------------------
    current = field_map.get("management.adaptive_management_plan", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"adaptive management", combined_text)
            or re.search(r"adaptive management framework", combined_text)
            or re.search(r"review.*operational assumptions", combined_text)
            or re.search(r"revise.*monitoring approach", combined_text)
        ):
            upsert_field(
                field_map,
                path="management.adaptive_management_plan",
                value=True,
                evidence="Heuristic match: adaptive management framework is explicitly described.",
                extractor="management_mapper",
                fill_method="heuristic",
                confidence=0.96,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # management.information_sharing_plan
    # ------------------------------------------------------------
    current = field_map.get("management.information_sharing_plan", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"information sharing", combined_text)
            or re.search(r"communicat", combined_text)
            or re.search(r"report findings", combined_text)
            or re.search(r"share.*results", combined_text)
            or re.search(r"internal review", combined_text)
        ):
            upsert_field(
                field_map,
                path="management.information_sharing_plan",
                value=True,
                evidence="Heuristic match: information sharing / communication procedures are explicitly described.",
                extractor="management_mapper",
                fill_method="heuristic",
                confidence=0.91,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # management.emergency_response_plan
    # ------------------------------------------------------------
    current = field_map.get("management.emergency_response_plan", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"emergency response", combined_text)
            or re.search(r"incident response", combined_text)
            or re.search(r"contingency", combined_text)
            or re.search(r"response procedures", combined_text)
        ):
            upsert_field(
                field_map,
                path="management.emergency_response_plan",
                value=True,
                evidence="Heuristic match: emergency response / contingency procedures are explicitly described.",
                extractor="management_mapper",
                fill_method="heuristic",
                confidence=0.94,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # management.pause_or_stop_conditions
    # ------------------------------------------------------------
    current = field_map.get("management.pause_or_stop_conditions", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"pause", combined_text)
            or re.search(r"stop operations", combined_text)
            or re.search(r"suspend operations", combined_text)
            or re.search(r"conditions for resumption", combined_text)
            or re.search(r"operations may be paused", combined_text)
        ):
            upsert_field(
                field_map,
                path="management.pause_or_stop_conditions",
                value=True,
                evidence="Heuristic match: pause/stop/suspension and resumption conditions are explicitly described.",
                extractor="management_mapper",
                fill_method="heuristic",
                confidence=0.95,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # management.monitoring_triggers
    # ------------------------------------------------------------
    current = field_map.get("management.monitoring_triggers", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"trigger", combined_text)
            or re.search(r"threshold", combined_text)
            or re.search(r"exceedance", combined_text)
            or re.search(r"review points", combined_text)
            or re.search(r"if .* detected", combined_text)
            or re.search(r"conditions for resumption", combined_text)
        ):
            upsert_field(
                field_map,
                path="management.monitoring_triggers",
                value=True,
                evidence="Heuristic match: thresholds/triggers/review conditions for corrective action are explicitly described.",
                extractor="management_mapper",
                fill_method="heuristic",
                confidence=0.84,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))


def run_management_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()

    if not fields:
        return {
            "normalized_fields": [],
            "raw_extraction": {"fields": []},
        }

    prompt = build_domain_prompt(
        domain_name="management",
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
        extractor_name="management_mapper",
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

    # ------------------------------------------------------------
    # INFERRED adaptive_management_plan (CRITICAL FIX)
    # ------------------------------------------------------------
    current = field_map.get("management.adaptive_management_plan", {}).get("value")

    if current in (None, False, "", []):
        info = field_map.get("management.information_sharing_plan", {}).get("value")
        emergency = field_map.get("management.emergency_response_plan", {}).get("value")
        pause = field_map.get("management.pause_or_stop_conditions", {}).get("value")
        triggers = field_map.get("management.monitoring_triggers", {}).get("value")

        # CORE LOGIC:
        # if at least 2 structural components exist → adaptive management exists
        components_true = sum([
            bool(info),
            bool(emergency),
            bool(pause),
            bool(triggers),
        ])

        if components_true >= 2:
            upsert_field(
                field_map,
                path="management.adaptive_management_plan",
                value=True,
                evidence="Inferred: adaptive management system exists because multiple components (information sharing, emergency response, pause/stop conditions, monitoring triggers) are explicitly documented.",
                extractor="management_mapper",
                fill_method="heuristic_inference",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="inferred",
            )
