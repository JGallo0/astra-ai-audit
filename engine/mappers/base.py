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

CRITICAL_TRUE_HEURISTIC_PATHS = {
    "eligibility.net_negative_claim",
    "production.reactor_design_diagram",
    "production.engineering_design_diagram",
    "production.maintenance_plan",
    "production.maintenance_schedule",
    "production.sensor_inventory",
    "production.sensor_locations",
    "sampling.batch_definition_days",
    "sampling.sampling_plan_defined",
}

ABSENCE_PATTERNS = [
    r"\bno evidence\b",
    r"\bno explicit evidence\b",
    r"\bno mention\b",
    r"\bnot mentioned\b",
    r"\bnot described\b",
    r"\bnot provided\b",
    r"\bnot specified\b",
    r"\bnot identified\b",
    r"\bnot found\b",
    r"\bno explicit reference\b",
    r"\bno direct evidence\b",
    r"\bno clear evidence\b",
]


def clean_evidence(text: Any, max_len: int = 280) -> str:
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

    if any(k in txt for k in [
        "annex",
        "appendix",
        "attached",
        "attachment",
        "supporting document",
        "technical annex",
        "uploaded file",
        "included in annex",
    ]):
        return "referenced_attachment"

    if any(k in txt for k in [
        "heuristic match",
        "inferred",
        "implied",
    ]):
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
        "batch-level",
        "net removals",
        "net negative",
        "kgco2eq",
        "iso/iec 17025",
        "lab report",
        "chain of custody",
        "lca",
        "temperature sensors",
        "pressure monitoring",
        "gas flow measurement",
    ]
    moderate_markers = [
        "documented",
        "described",
        "included",
        "provided",
        "attached",
        "evidenced",
        "monitoring",
        "testing",
        "archived",
    ]

    if any(k in txt for k in strong_markers):
        return "strong"
    if any(k in txt for k in moderate_markers):
        return "moderate"

    return "moderate" if value is not None else "weak"


def _is_absence_style_evidence(evidence: str) -> bool:
    txt = (evidence or "").lower()
    return any(re.search(p, txt, re.IGNORECASE) for p in ABSENCE_PATTERNS)


def _normalize_absence_false_to_none(value: Any, evidence: str) -> Any:
    if value is False and _is_absence_style_evidence(evidence):
        return None
    return value


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
        evidence = clean_evidence(item.get("evidence"))
        value = normalize_field_value(field_def, item.get("value"))
        value = _normalize_absence_false_to_none(value, evidence)

        confidence = safe_float(item.get("confidence"))
        source = item.get("source") or "project"

        evidence_mode = item.get("evidence_mode") or infer_evidence_mode(evidence)
        evidence_strength = item.get("evidence_strength") or infer_evidence_strength(evidence, value)

        # --- RASTREABILIDADE: captura citação de origem do documento ---
        raw_citation = item.get("citation") or {}
        citation = {
            "document": clean_evidence(raw_citation.get("document", ""), max_len=200),
            "page": str(raw_citation.get("page", "")).strip(),
            "excerpt": clean_evidence(raw_citation.get("excerpt", ""), max_len=300),
        }

        normalized.append({
            "path": path,
            "value": value,
            "evidence": evidence,
            "citation": citation,
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
    citation: Optional[Dict[str, str]] = None,
) -> None:
    existing = field_map.get(path, {})

    candidate = {
        "path": path,
        "value": value,
        "evidence": clean_evidence(evidence) or existing.get("evidence", ""),
        "citation": citation or existing.get("citation", {}),
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
    path = item.get("path")
    value = item.get("value")
    fill_method = item.get("fill_method", "fallback")
    extractor = item.get("extractor", "")
    evidence = item.get("evidence", "") or ""
    confidence = safe_float(item.get("confidence")) or 0.0

    evidence_strength_rank = EVIDENCE_STRENGTH_ORDER.get(item.get("evidence_strength", "weak"), 0)
    evidence_mode_rank = EVIDENCE_MODE_ORDER.get(item.get("evidence_mode", "inferred"), 0)
    fill_method_rank = FILL_METHOD_ORDER.get(fill_method, 0)

    # Penalize nulls and absence-style false responses from LLM
    value_presence_rank = 1 if value is not None else 0
    absence_false_penalty = 1 if (value is False and _is_absence_style_evidence(evidence)) else 0

    # Critical-path override:
    # explicit heuristic true should beat LLM false/null for these paths
    critical_true_boost = 0
    if (
        path in CRITICAL_TRUE_HEURISTIC_PATHS
        and value not in (None, False, "", [])
        and fill_method == "heuristic"
    ):
        critical_true_boost = 5

    # Heuristic explicit/direct strong signals should outrank generic LLM negatives
    explicit_positive_boost = 0
    if value not in (None, False, "", []):
        if evidence_mode_rank >= 2:
            explicit_positive_boost += 1
        if evidence_strength_rank >= 2:
            explicit_positive_boost += 1

    fallback_penalty = 0 if extractor == "fallback_mapper" else 1

    return (
        critical_true_boost,
        explicit_positive_boost,
        value_presence_rank,
        -absence_false_penalty,
        evidence_strength_rank,
        evidence_mode_rank,
        fill_method_rank,
        confidence,
        fallback_penalty,
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
6. If the document is pre-operational, do NOT assume measured operational evidence exists.
7. Do NOT output false merely because the evidence was not found in the provided excerpt.
   If not found or unclear, return null.
8. Include short evidence text and confidence between 0 and 1.
9. Use source="project" unless the field is clearly methodological in nature.
10. CITATION (MANDATORY): For every field where you find evidence, populate the citation object
    with the document name, page/section number, and a short literal excerpt (max 200 chars)
    copied verbatim from the source text. This is required for audit traceability.
    If no evidence is found, set citation to {{}}.

DOMAIN INSTRUCTIONS:
{domain_instructions}

OUTPUT FORMAT:
{{
  "fields": [
    {{
      "path": "example.path",
      "value": true,
      "evidence": "short evidence summary",
      "citation": {{
        "document": "filename or document title",
        "page": "page or section number",
        "excerpt": "verbatim excerpt from source text (max 200 chars)"
      }},
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
