from typing import Any, Dict, List, Optional, Tuple
from schemas.project_schema import get_empty_project_data
from engine.inference import run_inference_layer
from engine.mappers import run_mapper_pipeline
from engine.mappers.consistency import run_consistency_checks
from engine.extraction_schema import EXTRACTION_FIELDS
from engine.normalization import normalize_field_value

# --- CANONICAL PATH MAPPING ---

CANONICAL_PATH_MAP = {
    "biochar_characterization": "biochar.characterization",
    "biochar_characterization.carbon_content": "biochar.characterization.carbon_content",
    "biochar_characterization.h_c_ratio": "biochar.characterization.h_c_ratio",
    "biochar_characterization.o_c_ratio": "biochar.characterization.o_c_ratio",
    "biochar_characterization.sampling_method": "biochar.characterization.sampling_method",
    "biochar_characterization.sampling_frequency": "biochar.characterization.sampling_frequency",
    "biochar_characterization.approach_description": "biochar.characterization.approach_description",
    "biochar_characterization.ongoing_monitoring_plan": "biochar.characterization.ongoing_monitoring_plan",
}


def canonicalize_path(path: str) -> str:
    """
    Normaliza paths legados para o formato canônico do schema.
    """

    # Match direto (mais específico primeiro)
    if path in CANONICAL_PATH_MAP:
        return CANONICAL_PATH_MAP[path]

    # Match por prefixo (ex: biochar_characterization.*)
    for old_prefix, new_prefix in CANONICAL_PATH_MAP.items():
        if path.startswith(old_prefix + "."):
            return path.replace(old_prefix, new_prefix, 1)

    return path

def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    keys = path.split(".")
    cursor = data

    for key in keys[:-1]:
        if key not in cursor or not isinstance(cursor[key], dict):
            cursor[key] = {}
        cursor = cursor[key]

    cursor[keys[-1]] = value
    

def _build_field_schema_index() -> Dict[str, Dict[str, Any]]:
    return {
        field["path"]: field
        for field in EXTRACTION_FIELDS
        if field.get("path")
    }


def _normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _action_priority(action: str) -> int:
    action = _normalize_text(action)

    priorities = {
        "semantic_override": 60,
        "override": 55,
        "reclassify": 50,
        "set": 40,
        "fill": 35,
        "fallback": 10,
        "invalidate": 0,
        "clear": 0,
        "ignore": 0,
    }
    return priorities.get(action, 30)


def _evidence_mode_priority(mode: str) -> int:
    mode = _normalize_text(mode)

    priorities = {
        "direct": 40,
        "inferred": 25,
        "fallback": 10,
    }
    return priorities.get(mode, 15)


def _evidence_strength_priority(strength: str) -> int:
    strength = _normalize_text(strength)

    priorities = {
        "strong": 30,
        "moderate": 20,
        "weak": 10,
    }
    return priorities.get(strength, 0)


def _candidate_score(item: Dict[str, Any]) -> float:
    confidence = _safe_float(item.get("confidence"), 0.0)
    action = item.get("resolution_action", "set")
    evidence_mode = item.get("evidence_mode", "")
    evidence_strength = item.get("evidence_strength", "")
    citation = item.get("citation") or {}

    score = 0.0
    score += _action_priority(action)
    score += _evidence_mode_priority(evidence_mode)
    score += _evidence_strength_priority(evidence_strength)
    score += confidence * 100.0

    if item.get("fill_method") == "fallback":
        score -= 15.0

    has_citation_document = bool((citation.get("document") or "").strip()) if isinstance(citation, dict) else False
    has_citation_excerpt = bool((citation.get("excerpt") or "").strip()) if isinstance(citation, dict) else False
    if has_citation_document:
        score += 3.0
    if has_citation_excerpt:
        score += 2.0
    if _normalize_text(evidence_mode) == "direct" and not has_citation_document:
        score -= 10.0

    if item.get("value") is None:
        score -= 1000.0

    return score


def _collect_invalidated_paths(
    normalized_fields: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    invalidated: Dict[str, List[Dict[str, Any]]] = {}

    for item in normalized_fields:
        action = _normalize_text(item.get("resolution_action", "set"))

        related_paths: List[str] = []
        related_paths.extend(_normalize_list(item.get("invalidates_paths")))
        related_paths.extend(_normalize_list(item.get("supersedes_paths")))

        reclassify_from = item.get("reclassify_from")
        if reclassify_from:
            related_paths.append(str(reclassify_from).strip())

        if action in {"reclassify", "semantic_override", "override", "invalidate", "clear"}:
            for path in related_paths:
                canonical_path = canonicalize_path(path)
                invalidated.setdefault(canonical_path, []).append(
                    {
                        "by_path": canonicalize_path(item.get("path") or ""),
                        "action": action,
                        "rule": item.get("inference_rule_id") or item.get("extractor"),
                        "confidence": item.get("confidence"),
                    }
                )

    return invalidated


def _group_candidates_by_path(
    normalized_fields: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for item in normalized_fields:
        path = item.get("path")
        if not path:
            continue
        canonical_path = canonicalize_path(path)

        action = _normalize_text(item.get("resolution_action", "set"))

        if action in {"invalidate", "clear", "ignore"}:
            continue

        if item.get("value") is None:
            continue

        candidate = dict(item)
        candidate["original_path"] = path
        candidate["path"] = canonical_path
        grouped.setdefault(canonical_path, []).append(candidate)

    return grouped


def _resolve_field_candidates(
    normalized_fields: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    invalidated_paths = _collect_invalidated_paths(normalized_fields)
    grouped = _group_candidates_by_path(normalized_fields)

    resolved_fields: Dict[str, Any] = {}
    resolution_log: List[Dict[str, Any]] = []

    for path, candidates in grouped.items():
        if path in invalidated_paths:
            override_candidates = [
                c for c in candidates
                if _normalize_text(c.get("resolution_action")) in {
                    "semantic_override",
                    "override",
                    "reclassify",
                }
            ]

            if override_candidates:
                ranked = sorted(
                    override_candidates,
                    key=_candidate_score,
                    reverse=True,
                )

                winner = ranked[0]
                resolved_fields[path] = winner.get("value")

                resolution_log.append(
                    {
                        "path": path,
                        "status": "resolved_via_override",
                        "winner": {
                            "value": winner.get("value"),
                            "extractor": winner.get("extractor"),
                            "confidence": winner.get("confidence"),
                            "evidence_mode": winner.get("evidence_mode"),
                            "evidence_strength": winner.get("evidence_strength"),
                            "fill_method": winner.get("fill_method"),
                            "resolution_action": winner.get("resolution_action", "set"),
                            "inference_rule_id": winner.get("inference_rule_id"),
                            "citation": winner.get("citation", {}),
                        },
                        "invalidated_by": invalidated_paths[path],
                        "candidate_count": len(candidates),
                    }
                )
                continue

            resolution_log.append(
                {
                    "path": path,
                    "status": "invalidated_by_other_rule",
                    "invalidated_by": invalidated_paths[path],
                    "candidate_count": len(candidates),
                }
            )
            continue

        ranked = sorted(
            candidates,
            key=_candidate_score,
            reverse=True,
        )

        winner = ranked[0]
        resolved_fields[path] = winner.get("value")

        resolution_log.append(
            {
                "path": path,
                "status": "resolved",
                "winner": {
                    "value": winner.get("value"),
                    "extractor": winner.get("extractor"),
                    "confidence": winner.get("confidence"),
                    "evidence_mode": winner.get("evidence_mode"),
                    "evidence_strength": winner.get("evidence_strength"),
                    "fill_method": winner.get("fill_method"),
                    "resolution_action": winner.get("resolution_action", "set"),
                    "inference_rule_id": winner.get("inference_rule_id"),
                    "citation": winner.get("citation", {}),
                },
                "losers": [
                    {
                        "value": item.get("value"),
                        "extractor": item.get("extractor"),
                        "confidence": item.get("confidence"),
                        "evidence_mode": item.get("evidence_mode"),
                        "evidence_strength": item.get("evidence_strength"),
                        "fill_method": item.get("fill_method"),
                        "resolution_action": item.get("resolution_action", "set"),
                        "inference_rule_id": item.get("inference_rule_id"),
                    }
                    for item in ranked[1:]
                ],
                "candidate_count": len(ranked),
            }
        )
    return resolved_fields, resolution_log, invalidated_paths


def build_project_data_from_extraction(
    normalized_fields: List[Dict[str, Any]],
    return_resolution_artifacts: bool = False,
) -> Any:
    data = get_empty_project_data()

    resolved_fields, resolution_log, invalidated_paths = _resolve_field_candidates(
        normalized_fields
    )

    field_schema_index = _build_field_schema_index()

    # Monta indice de citacoes: {path -> citation} a partir do resolution_log
    field_citations: Dict[str, Any] = {}
    for entry in resolution_log:
        path = canonicalize_path(entry.get("path") or "")
        winner = entry.get("winner", {})
        citation = winner.get("citation")
        if path and citation:
            field_citations[path] = citation

    for path, value in resolved_fields.items():
        canonical_path = canonicalize_path(path)
        field_def = field_schema_index.get(canonical_path) or field_schema_index.get(path)

        if field_def:
            normalized_value = normalize_field_value(field_def, value)
        else:
            normalized_value = value

        if normalized_value is None:
            continue

        set_nested_value(data, canonical_path, normalized_value)

    if return_resolution_artifacts:
        return {
            "project_data": data,
            "resolved_fields": resolved_fields,
            "field_resolution_log": resolution_log,
            "field_citations": field_citations,
            "invalidated_paths": invalidated_paths,
        }

    return data


def extract_project_data_from_contexts(
    ai_client,
    project_context: str,
    methodology_context: str,
    project_hits: Optional[List[Dict[str, Any]]] = None,
    methodology_hits: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    try:
        pipeline_output = run_mapper_pipeline(
            ai_client=ai_client,
            project_context=project_context,
            methodology_context=methodology_context,
            project_hits=project_hits or [],
            methodology_hits=methodology_hits or [],
        )

        if not isinstance(pipeline_output, dict):
            raise TypeError(
                f"run_mapper_pipeline returned {type(pipeline_output).__name__}, expected dict"
            )

        normalized_fields = pipeline_output.get("normalized_fields", []) or []
        raw_extraction_bundle = pipeline_output.get("raw_extraction_bundle", {}) or {}

        inference_output = run_inference_layer(
            normalized_fields=normalized_fields,
            raw_extraction_bundle=raw_extraction_bundle,
            project_context=project_context,
            methodology_context=methodology_context,
        )

        if not isinstance(inference_output, dict):
            raise TypeError(
                f"run_inference_layer returned {type(inference_output).__name__}, expected dict"
            )

        normalized_fields = inference_output.get("normalized_fields", []) or normalized_fields
        inference_events = inference_output.get("inference_events", []) or []

        build_output = build_project_data_from_extraction(
            normalized_fields,
            return_resolution_artifacts=True,
        )

        project_data = build_output["project_data"]

        consistency_output = run_consistency_checks(
            project_data=project_data,
            normalized_fields=normalized_fields,
        )

        return {
            "project_data": project_data,
            "normalized_fields": normalized_fields,
            "raw_extraction": raw_extraction_bundle,
            "inference_events": inference_events,
            "resolved_fields": build_output.get("resolved_fields", {}),
            "field_resolution_log": build_output.get("field_resolution_log", []),
            "field_citations": build_output.get("field_citations", {}),
            "invalidated_paths": build_output.get("invalidated_paths", {}),
            "consistency_flags": consistency_output.get("consistency_flags", []),
            "consistency_notes": consistency_output.get("consistency_notes", []),
        }

    except Exception as e:
        raise RuntimeError(f"extract_project_data_from_contexts failed: {e}")
