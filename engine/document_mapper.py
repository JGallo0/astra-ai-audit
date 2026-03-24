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

Return ONLY valid JSON.
Do not add commentary, markdown, or explanations.
If a field is not supported by evidence, return null.
For list_string fields, return an array of strings.
For boolean fields, return true, false, or null.

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
