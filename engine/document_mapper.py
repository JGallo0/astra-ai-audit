# engine/document_mapper.py

import json
from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.normalization import normalize_field_value
from schemas.project_schema import get_empty_project_data


def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    keys = path.split(".")
    cursor = data

    for key in keys[:-1]:
        if key not in cursor or not isinstance(cursor[key], dict):
            cursor[key] = {}
        cursor = cursor[key]

    cursor[keys[-1]] = value


def build_extraction_prompt(fields: List[Dict[str, Any]]) -> str:
    field_specs = []

    for f in fields:
        item = {
            "path": f["path"],
            "type": f["type"],
            "description": f["description"],
        }
        if "allowed_values" in f:
            item["allowed_values"] = f["allowed_values"]
        field_specs.append(item)

    return f"""
You are extracting structured carbon project data from documentary evidence.

Your task is to populate structured fields using ONLY the evidence provided.

Return ONLY valid JSON.
Do not add commentary, markdown, or explanations outside the JSON.

Important extraction rules:

1. Use documentary evidence conservatively, but do not be overly literal.
2. If the document explicitly states that a plan, diagram, appendix, attachment, contract, log,
   drawing, report, file, or supporting document exists, you MAY treat the corresponding
   boolean/document-existence field as supported.
3. If the document provides clear textual evidence of a concept, mark the field accordingly
   even if the exact field name is not used.
4. If the text only says something will be implemented in the future, or "once available",
   do NOT mark that as fully evidenced. Prefer null in such cases unless the field is explicitly
   about a future plan.
5. Distinguish between:
   - explicit current evidence
   - attachment/appendix reference
   - future intention
6. For booleans:
   - return true when evidence clearly supports existence/presence/compliance
   - return false only when the document clearly indicates absence or contradiction
   - return null when evidence is insufficient or ambiguous
7. For int fields:
   - convert clear textual evidence into integers where appropriate
   - example: "24-hour production window" -> 1 day
8. For list_string fields:
   - return a list of concise strings extracted from the evidence
9. Prefer project evidence for project-specific fields, but methodology evidence may clarify
   interpretation.
10. If evidence exists only by reference to an attachment or appendix, mention that explicitly
    in the evidence text.

Special guidance for common patterns:
- "Attached", "Appendix", "Supporting documents", "diagram", "drawing", "PFD", "P&ID",
  "layout drawing", "contract", "lab report", "byproduct log", "SCADA", "archived records",
  "sampling frequency", "per batch", "maintenance schedule", "sensor calibration", "ISO/IEC 17025"
  should all be treated as strong signals when relevant.
- "net negative", "environmentally additional", "financially additional", "regulatorily additional",
  "counterfactual emissions of baseline is zero", "chosen 200 years", "annual average soil temperature"
  are strong signals for the corresponding eligibility/additionality/durability fields.
- "will be implemented", "once available", "planned", "future" are NOT strong signals for current evidence.

Required output format:
{{
  "fields": [
    {{
      "path": "methodology.standard",
      "value": "Isometric",
      "evidence": "short quote or concise evidence summary",
      "source": "project"
    }}
  ]
}}

Fields to extract:
{json.dumps(field_specs, ensure_ascii=False, indent=2)}
""".strip()


def normalize_extracted_fields(
    extracted_payload: Dict[str, Any],
    fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    field_map = {f["path"]: f for f in fields}
    normalized = []

    for item in extracted_payload.get("fields", []):
        path = item.get("path")
        if path not in field_map:
            continue

        field_def = field_map[path]
        value = normalize_field_value(field_def, item.get("value"))

        normalized.append({
            "path": path,
            "value": value,
            "evidence": item.get("evidence"),
            "source": item.get("source"),
        })

    return normalized


def build_project_data_from_extraction(
    normalized_fields: List[Dict[str, Any]],
) -> Dict[str, Any]:
    data = get_empty_project_data()

    for item in normalized_fields:
        value = item["value"]
        if value is None:
            continue
        set_nested_value(data, item["path"], value)

    return data


def extract_project_data_from_contexts(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    prompt = build_extraction_prompt(EXTRACTION_FIELDS)

    full_prompt = f"""
PROJECT EVIDENCE
----------------
{project_context}

METHODOLOGY EVIDENCE
--------------------
{methodology_context}

{prompt}
""".strip()

    raw = ai_client(full_prompt)

    if isinstance(raw, dict):
        extracted_payload = raw
    else:
        extracted_payload = json.loads(raw)

    normalized = normalize_extracted_fields(extracted_payload, EXTRACTION_FIELDS)
    project_data = build_project_data_from_extraction(normalized)

    return {
        "project_data": project_data,
        "normalized_fields": normalized,
        "raw_extraction": extracted_payload,
    }
