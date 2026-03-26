# engine/inference/base.py

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


STRONG_CONFIDENCE_THRESHOLD = 0.85
MODERATE_CONFIDENCE_THRESHOLD = 0.65


# =========================================================
# BASIC UTILS
# =========================================================

def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def safe_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value

    text = normalize_text(value)

    if text in {"true", "yes", "y", "1"}:
        return True
    if text in {"false", "no", "n", "0"}:
        return False

    return None


# =========================================================
# FIELD RESOLUTION HELPERS
# =========================================================

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
        evidence_strength = normalize_text(item.get("evidence_strength"))

        score = confidence

        if evidence_mode == "direct":
            score += 0.2
        elif evidence_mode == "inferred":
            score += 0.1

        if evidence_strength == "strong":
            score += 0.1
        elif evidence_strength == "moderate":
            score += 0.05

        if item.get("fill_method") == "fallback":
            score -= 0.2

        return score

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


# =========================================================
# INFERENCE FIELD BUILDER (CORE)
# =========================================================

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
    # 🔴 NOVOS CAMPOS ESTRUTURAIS
    resolution_action: str = "set",
    reclassify_from: Optional[str] = None,
    invalidates_paths: Optional[List[str]] = None,
    supersedes_paths: Optional[List[str]] = None,
    overwrite: bool = False,
) -> List[Dict[str, Any]]:
    """
    Adiciona um campo inferido de forma estruturada e auditável.

    Esse método é o ponto central da inference layer.
    """

    existing = get_best_field(normalized_fields, path)

    # -----------------------------------------------------
    # PROTEÇÃO CONTRA SOBRESCRITA INDEVIDA
    # -----------------------------------------------------
    if existing and not overwrite:
        existing_conf = safe_float(existing.get("confidence")) or 0.0
        existing_mode = normalize_text(existing.get("evidence_mode"))

        if existing_mode == "direct" and existing_conf >= STRONG_CONFIDENCE_THRESHOLD:
            return normalized_fields

    # -----------------------------------------------------
    # NORMALIZAÇÃO DOS CAMPOS RELACIONADOS
    # -----------------------------------------------------
    invalidates_paths = invalidates_paths or []
    supersedes_paths = supersedes_paths or []
    inputs_used = inputs_used or []

    # reclassificação implica invalidação automática
    if reclassify_from:
        invalidates_paths = list(set(invalidates_paths + [reclassify_from]))

    # -----------------------------------------------------
    # EVENTO ESTRUTURADO
    # -----------------------------------------------------
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
        "inputs_used": inputs_used,
        # 🔴 CAMPOS NOVOS
        "resolution_action": resolution_action,
        "reclassify_from": reclassify_from,
        "invalidates_paths": invalidates_paths,
        "supersedes_paths": supersedes_paths,
    }

    updated_fields = deepcopy(normalized_fields)
    updated_fields.append(event)
    inference_events.append(event)

    return updated_fields


# =========================================================
# PROJECT TEXT HELPERS
# =========================================================

def project_contains_any(project_context: str, keywords: List[str]) -> bool:
    text = normalize_text(project_context)
    return any(k.lower() in text for k in keywords)


def project_contains_all(project_context: str, keywords: List[str]) -> bool:
    text = normalize_text(project_context)
    return all(k.lower() in text for k in keywords)


def count_project_keyword_hits(project_context: str, keywords: List[str]) -> int:
    text = normalize_text(project_context)
    return sum(1 for kw in keywords if kw.lower() in text)


# =========================================================
# BASE CLASS
# =========================================================

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
