from copy import deepcopy
from typing import Any, Dict, List


VALID_AUDIT_STATUSES = [
    "Conforme",
    "Parcialmente conforme",
    "Não conforme",
    "Não evidenciado",
    "Inconsistência documental",
    "Erro de análise",
]

VALID_RISK_LEVELS = [
    "baixo",
    "medio",
    "alto",
]


AUDIT_RESULT_COLUMNS = [
    "requirement_id",
    "module",
    "title",
    "status",
    "risk",
    "score",
    "confidence",
    "project_evidence",
    "methodology_basis",
    "gap",
    "recommendation",
    "notes",
]


DEFAULT_REQUIREMENT_SCHEMA: Dict[str, Any] = {
    "id": "",
    "module": "",
    "title": "",
    "description": "",
    "rationale": "",
    "keywords": [],
    "weight": 1,
    "evaluation_criteria": [],
    "expected_evidence_types": [],
}


DEFAULT_AUDIT_RESULT_SCHEMA: Dict[str, Any] = {
    "requirement_id": "",
    "module": "",
    "title": "",
    "status": "Não evidenciado",
    "risk": "alto",
    "score": 0,
    "confidence": 0,
    "project_evidence": "",
    "methodology_basis": "",
    "gap": "",
    "recommendation": "",
    "notes": "",
}


DEFAULT_AUDIT_SUMMARY_SCHEMA: Dict[str, Any] = {
    "total_requirements": 0,
    "overall_score": 0.0,
    "overall_confidence": 0.0,
    "status_counts": {},
    "risk_counts": {},
    "module_scores": {},
    "module_confidence": {},
}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_int(
    value: Any,
    default: int = 0,
    min_value: int = 0,
    max_value: int = 100,
) -> int:
    try:
        parsed = int(round(float(value)))
    except Exception:
        parsed = default
    return max(min_value, min(max_value, parsed))


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def make_requirement_schema(requirement: Dict[str, Any] | None = None) -> Dict[str, Any]:
    out = deepcopy(DEFAULT_REQUIREMENT_SCHEMA)

    if not requirement:
        return out

    out["id"] = _safe_str(requirement.get("id", ""))
    out["module"] = _safe_str(requirement.get("module", ""))
    out["title"] = _safe_str(requirement.get("title", ""))
    out["description"] = _safe_str(requirement.get("description", ""))
    out["rationale"] = _safe_str(requirement.get("rationale", ""))
    out["keywords"] = _safe_list(requirement.get("keywords", []))
    out["weight"] = _safe_int(requirement.get("weight", 1), default=1, min_value=1, max_value=100)
    out["evaluation_criteria"] = _safe_list(requirement.get("evaluation_criteria", []))
    out["expected_evidence_types"] = _safe_list(requirement.get("expected_evidence_types", []))

    return out


def make_audit_result_schema(
    requirement: Dict[str, Any] | None = None,
    overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    out = deepcopy(DEFAULT_AUDIT_RESULT_SCHEMA)

    if requirement:
        out["requirement_id"] = _safe_str(requirement.get("id", ""))
        out["module"] = _safe_str(requirement.get("module", ""))
        out["title"] = _safe_str(requirement.get("title", ""))

    if overrides:
        for key, value in overrides.items():
            if key not in out:
                continue
            out[key] = value

    out["requirement_id"] = _safe_str(out.get("requirement_id", ""))
    out["module"] = _safe_str(out.get("module", ""))
    out["title"] = _safe_str(out.get("title", ""))

    status = _safe_str(out.get("status", "Não evidenciado"))
    out["status"] = status if status in VALID_AUDIT_STATUSES else "Erro de análise"

    risk = _safe_str(out.get("risk", "alto")).lower()
    out["risk"] = risk if risk in VALID_RISK_LEVELS else "alto"

    out["score"] = _safe_int(out.get("score", 0), default=0, min_value=0, max_value=100)
    out["confidence"] = _safe_int(out.get("confidence", 0), default=0, min_value=0, max_value=100)

    out["project_evidence"] = _safe_str(out.get("project_evidence", ""))
    out["methodology_basis"] = _safe_str(out.get("methodology_basis", ""))
    out["gap"] = _safe_str(out.get("gap", ""))
    out["recommendation"] = _safe_str(out.get("recommendation", ""))
    out["notes"] = _safe_str(out.get("notes", ""))

    return out


def make_empty_audit_summary() -> Dict[str, Any]:
    return deepcopy(DEFAULT_AUDIT_SUMMARY_SCHEMA)


def validate_requirement_schema(requirement: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if not _safe_str(requirement.get("id", "")):
        errors.append("Requirement missing 'id'.")
    if not _safe_str(requirement.get("module", "")):
        errors.append(f"Requirement {requirement.get('id', '<unknown>')} missing 'module'.")
    if not _safe_str(requirement.get("title", "")):
        errors.append(f"Requirement {requirement.get('id', '<unknown>')} missing 'title'.")
    if not _safe_str(requirement.get("description", "")):
        errors.append(f"Requirement {requirement.get('id', '<unknown>')} missing 'description'.")

    weight = requirement.get("weight", 1)
    try:
        weight_value = int(weight)
        if weight_value < 1:
            errors.append(f"Requirement {requirement.get('id', '<unknown>')} has invalid 'weight'.")
    except Exception:
        errors.append(f"Requirement {requirement.get('id', '<unknown>')} has non-numeric 'weight'.")

    keywords = requirement.get("keywords", [])
    if keywords is not None and not isinstance(keywords, list):
        errors.append(f"Requirement {requirement.get('id', '<unknown>')} has invalid 'keywords' type.")

    return errors


def validate_audit_result_schema(result: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if not _safe_str(result.get("requirement_id", "")):
        errors.append("Audit result missing 'requirement_id'.")
    if not _safe_str(result.get("module", "")):
        errors.append(f"Audit result {result.get('requirement_id', '<unknown>')} missing 'module'.")
    if not _safe_str(result.get("title", "")):
        errors.append(f"Audit result {result.get('requirement_id', '<unknown>')} missing 'title'.")

    status = _safe_str(result.get("status", ""))
    if status not in VALID_AUDIT_STATUSES:
        errors.append(
            f"Audit result {result.get('requirement_id', '<unknown>')} has invalid status '{status}'."
        )

    risk = _safe_str(result.get("risk", "")).lower()
    if risk not in VALID_RISK_LEVELS:
        errors.append(
            f"Audit result {result.get('requirement_id', '<unknown>')} has invalid risk '{risk}'."
        )

    for field in ["score", "confidence"]:
        try:
            val = int(result.get(field, 0))
            if val < 0 or val > 100:
                errors.append(
                    f"Audit result {result.get('requirement_id', '<unknown>')} has invalid {field} '{val}'."
                )
        except Exception:
            errors.append(
                f"Audit result {result.get('requirement_id', '<unknown>')} has non-numeric {field}."
            )

    return errors


def ensure_result_column_order(result: Dict[str, Any]) -> Dict[str, Any]:
    ordered = {col: result.get(col, DEFAULT_AUDIT_RESULT_SCHEMA.get(col)) for col in AUDIT_RESULT_COLUMNS}
    extras = {k: v for k, v in result.items() if k not in ordered}
    ordered.update(extras)
    return ordered


def normalize_results_list(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for item in results or []:
        fixed = make_audit_result_schema(overrides=item)
        fixed = ensure_result_column_order(fixed)
        normalized.append(fixed)
    return normalized
