# engine/inference/base.py

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


STRONG_CONFIDENCE_THRESHOLD = 0.85
MODERATE_CONFIDENCE_THRESHOLD = 0.65


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def safe_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value

    text = normalize_text(value)
    if text in {"true", "yes", "y", "1"}:
        return True
    if text in {"false", "no", "n", "0"}:
        return False
    return None


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def field_to_dict_list(normalized_fields: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    index: Dict[str, List[Dict[str, Any]]] = {}
    for item in normalized_fields or []:
        path = item.get("path")
        if not path:
            continue
        index.setdefault(path, []).append(item)
    return index


def get_best_field(
    normalized_fields: List[Dict[str, Any]],
    path: str,
) -> Optional[Dict[str, Any]]:
    candidates = [x for x in normalized_fields if x.get("path") == path]
    if not candidates:
        return None

    def score(item: Dict[str, Any]) -> float:
        confidence = safe_float(item.get("confidence")) or 0.0
        evidence_mode = normalize_text(item.get("evidence_mode"))
        extractor = normalize_text(item.get("extractor"))

        bonus = 0.0
        if evidence_mode == "direct":
            bonus += 0.20
        elif evidence_mode == "inferred":
            bonus += 0.10

        if "fallback" in extractor:
            bonus -= 0.10

        return confidence + bonus

    candidates.sort(key=score, reverse=True)
    return candidates[0]


def get_best_value(
    normalized_fields: List[Dict[str, Any]],
    path: str,
    default: Any = None,
) -> Any:
    best = get_best_field(normalized_fields, path)
    if not best:
        return default
    return best.get("value", default)


def has_strong_evidence(
    normalized_fields: List[Dict[str, Any]],
    path: str,
) -> bool:
    best = get_best_field(normalized_fields, path)
    if not best:
        return False

    confidence = safe_float(best.get("confidence")) or 0.0
    evidence_mode = normalize_text(best.get("evidence_mode"))

    return (
        evidence_mode == "direct"
        and confidence >= STRONG_CONFIDENCE_THRESHOLD
    )


def has_moderate_or_strong_evidence(
    normalized_fields: List[Dict[str, Any]],
    path: str,
) -> bool:
    best = get_best_field(normalized_fields, path)
    if not best:
        return False

    confidence = safe_float(best.get("confidence")) or 0.0
    return confidence >= MODERATE_CONFIDENCE_THRESHOLD


def path_exists_with_nonempty_value(
    normalized_fields: List[Dict[str, Any]],
    path: str,
) -> bool:
    best = get_best_field(normalized_fields, path)
    if not best:
        return False

    value = best.get("value")
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, list) and not value:
        return False

    return True


def append_inference_field(
    normalized_fields: List[Dict[str, Any]],
    inference_events: List[Dict[str, Any]],
    *,
    path: str,
    value: Any,
    evidence: str,
    source: str,
    confidence: float,
    evidence_strength: str,
    extractor: str,
    inference_rule_id: str,
    inputs_used: Optional[List[str]] = None,
    overwrite: bool = False,
) -> List[Dict[str, Any]]:
    existing = get_best_field(normalized_fields, path)

    if existing and not overwrite:
        existing_conf = safe_float(existing.get("confidence")) or 0.0
        existing_mode = normalize_text(existing.get("evidence_mode"))

        if existing_mode == "direct" and existing_conf >= STRONG_CONFIDENCE_THRESHOLD:
            return normalized_fields

    event = {
        "path": path,
        "value": value,
        "evidence": evidence,
        "source": source,
        "confidence": confidence,
        "evidence_strength": evidence_strength,
        "evidence_mode": "inferred",
        "extractor": extractor,
        "fill_method": "inference_rule",
        "inference_rule_id": inference_rule_id,
        "inputs_used": inputs_used or [],
    }

    updated_fields = deepcopy(normalized_fields)
    updated_fields.append(event)
    inference_events.append(event)
    return updated_fields


def project_contains_any(project_context: str, keywords: List[str]) -> bool:
    text = normalize_text(project_context)
    return any(k.lower() in text for k in keywords)


def project_contains_all(project_context: str, keywords: List[str]) -> bool:
    text = normalize_text(project_context)
    return all(k.lower() in text for k in keywords)


def count_project_keyword_hits(project_context: str, keywords: List[str]) -> int:
    text = normalize_text(project_context)
    count = 0
    for kw in keywords:
        if kw.lower() in text:
            count += 1
    return count


class BaseInferenceRule:
    rule_set_name = "base_inference"

    def run(
        self,
        normalized_fields: List[Dict[str, Any]],
        raw_extraction_bundle: Optional[Dict[str, Any]] = None,
        project_context: str = "",
        methodology_context: str = "",
    ) -> Dict[str, Any]:
        raise NotImplementedError
