# engine/mappers/base.py

import json
import re
from typing import Any, Dict, List, Optional

from engine.normalization import normalize_field_value


EVIDENCE_STRENGTH_ORDER = {
    "weak": 1,
    "moderate": 2,
    "strong": 3,
}

EVIDENCE_MODE_ORDER = {
    "inferred": 1,
    "referenced_attachment": 2,
    "direct": 3,
}

FILL_METHOD_ORDER = {
    "fallback": 1,
    "heuristic": 2,
    "llm": 3,
}


def clean_evidence(text: Any, max_len: int = 220) -> str:
    if text is None:
        return ""
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    return cleaned[:max_len]


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def parse_extraction_payload(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw

    if raw is None:
        return {"fields": []}

    if not isinstance(raw, str):
        raw = str(raw)

    raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {"fields": []}


def build_field_specs(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    specs = []
    for f in fields:
        item = {
            "path": f["path"],
            "type": f["type"],
            "description": f["description"],
        }
        if "allowed_values" in f:
            item["allowed_values"] = f["allowed_values"]
        specs.append(item)
    return specs


def filter_fields_by_prefixes(
    all_fields: List[Dict[str, Any]],
    prefixes: List[str],
) -> List[Dict[str, Any]]:
    return [
        f for f in all_fields
        if any(f["path"].startswith(prefix) for prefix in prefixes)
    ]


def filter_fields_by_paths(
    all_fields: List[Dict[str, Any]],
    paths: List[str],
) -> List[Dict[str, Any]]:
    path_set = set(paths)
    return [f for f in all_fields if f["path"] in path_set]


def infer_evidence_mode(evidence: str) -> str:
    txt = (evidence or "").lower()

    if any(k in txt for k in ["annex", "appendix", "attached", "attachment", "supporting document"]):
        return "referenced_attachment"

    if any(k in txt for k in ["heuristic match", "inferred", "implied"]):
        return "inferred"

    return "direct"


def infer_evidence_strength(evidence: str, value: Any) -> str:
    txt = (evidence or "").lower()

    if value is None:
        return "weak"

    strong_markers = [
        "annex",
        "appendix",
        "pfd",
        "p&id",
        "maintenance schedule",
        "production batch",
        "net removals",
        "iso/iec 17025",
        "lab report",
        "chain of custody",
        "lca",
    ]
    moderate_markers = [
        "documented",
        "described",
        "included",
        "provided",
        "attached",
        "evidenced",
    ]

    if any(k in txt for k in strong_markers):
        return "strong"
    if any(k in txt for k in moderate_markers):
        return "moderate"

    return "moderate" if value is not None else "weak"


def normalize_domain_fields(
    extracted_payload: Dict[str, Any],
    fields: List[Dict[str, Any]],
    extractor_name: str,
    fill_method: str = "llm",
) -> List[Dict[str, Any]]:
    field_map = {f["path"]: f for f in fields}
    normalized: List[Dict[str, Any]] = []

    for item in extracted_payload.get("fields", []):
        path = item.get("path")
        if path not in field_map:
            continue

        field_def = field_map[path]
        value = normalize_field_value(field_def, item.get("value"))
        evidence = clean_evidence(item.get("evidence"))
        confidence = safe_float(item.get("confidence"))
        source = item.get("source") or "project"

        evidence_mode = item.get("evidence_mode") or infer_evidence_mode(evidence)
        evidence_strength = item.get("evidence_strength") or infer_evidence_strength(evidence, value)

        normalized.append({
            "path": path,
            "value": value,
            "evidence": evidence,
            "source": source,
            "confidence": confidence,
            "evidence_strength": evidence_strength,
            "evidence_mode": evidence_mode,
            "extractor": extractor_name,
            "fill_method": fill_method,
        })

    return normalized


def upsert_field(
    field_map: Dict[str, Dict[str, Any]],
    path: str,
    value: Any,
    evidence: str,
    extractor: str,
    fill_method: str,
    source: str = "project",
    confidence: Optional[float] = None,
    evidence_strength: str = "moderate",
    evidence_mode: str = "inferred",
) -> None:
    existing = field_map.get(path, {})

    candidate = {
        "path": path,
        "value": value,
        "evidence": clean_evidence(evidence) or existing.get("evidence", ""),
        "source": source,
        "confidence": confidence if confidence is not None else existing.get("confidence"),
        "evidence_strength": evidence_strength,
        "evidence_mode": evidence_mode,
        "extractor": extractor,
        "fill_method": fill_method,
    }

    if path not in field_map:
        field_map[path] = candidate
        return

    field_map[path] = choose_better_item(field_map[path], candidate)


def _rank_item(item: Dict[str, Any]) -> tuple:
    return (
        EVIDENCE_STRENGTH_ORDER.get(item.get("evidence_strength", "weak"), 0),
        EVIDENCE_MODE_ORDER.get(item.get("evidence_mode", "inferred"), 0),
        1 if item.get("value") is not None else 0,
        safe_float(item.get("confidence")) or 0.0,
        FILL_METHOD_ORDER.get(item.get("fill_method", "fallback"), 0),
        0 if item.get("extractor") == "fallback_mapper" else 1,
    )


def choose_better_item(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return a if _rank_item(a) >= _rank_item(b) else b


def merge_normalized_fields(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}

    for item in items:
        path = item.get("path")
        if not path:
            continue

        if path not in merged:
            merged[path] = item
        else:
            merged[path] = choose_better_item(merged[path], item)

    return list(merged.values())


def find_missing_paths(
    normalized_fields: List[Dict[str, Any]],
    all_fields: List[Dict[str, Any]],
) -> List[str]:
    present = {
        item["path"]
        for item in normalized_fields
        if item.get("value") is not None
    }

    return [
        f["path"]
        for f in all_fields
        if f["path"] not in present
    ]


def build_domain_prompt(
    domain_name: str,
    fields: List[Dict[str, Any]],
    project_context: str,
    methodology_context: str,
    domain_instructions: str,
) -> str:
    field_specs = build_field_specs(fields)

    return f"""
You are a structured data extractor for a carbon project audit.

TASK:
Extract ONLY the fields for the domain: {domain_name}.

RULES:
1. Use ONLY project evidence to populate project-specific values.
2. Use methodology context only to interpret terms, not as proof of project compliance.
3. Return ONLY valid JSON.
4. If evidence is ambiguous, prefer null over false.
5. For booleans:
   - true only when evidence clearly supports the field
   - false only when the text clearly indicates contradiction/absence
   - null when uncertain
6. Include short evidence text and confidence between 0 and 1.
7. Use source="project" unless the field is clearly methodological in nature.

DOMAIN INSTRUCTIONS:
{domain_instructions}

OUTPUT FORMAT:
{{
  "fields": [
    {{
      "path": "example.path",
      "value": true,
      "evidence": "short evidence",
      "source": "project",
      "confidence": 0.91
    }}
  ]
}}

PROJECT EVIDENCE:
{project_context}

METHODOLOGY CONTEXT:
{methodology_context}

FIELDS TO EXTRACT:
{json.dumps(field_specs, ensure_ascii=False, indent=2)}
""".strip()
