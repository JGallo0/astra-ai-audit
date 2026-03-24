# engine/document_mapper.py

import json
from copy import deepcopy

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.normalization import normalize_field_value
from schemas.project_schema import get_empty_project_data


def set_nested_value(data, path, value):
    keys = path.split(".")
    cursor = data

    for key in keys[:-1]:
        if key not in cursor or not isinstance(cursor[key], dict):
            cursor[key] = {}
        cursor = cursor[key]

    cursor[keys[-1]] = value


def build_extraction_prompt(fields):
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
You are extracting structured carbon project data.

Return ONLY valid JSON.
Do not add commentary.
If a field is not supported by evidence, return null.

Required output format:
{{
  "fields": [
    {{
      "path": "methodology.standard",
      "value": "Isometric",
      "evidence": "short quote or summary",
      "source": "project or methodology"
    }}
  ]
}}

Fields to extract:
{json.dumps(field_specs, indent=2)}
""".strip()


def extract_fields_with_ai(
    ai_client,
    project_context,
    methodology_context,
    fields,
):
    """
    ai_client should be a callable or wrapper you already use in the app.
    It must return a raw string containing JSON.
    """

    prompt = build_extraction_prompt(fields)

    full_prompt = f"""
Project evidence:
{project_context}

Methodology evidence:
{methodology_context}

{prompt}
""".strip()

    raw = ai_client(full_prompt)
    parsed = json.loads(raw)
    return parsed


def normalize_extracted_fields(extracted_payload, fields):
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


def build_project_data_from_extraction(normalized_fields):
    data = get_empty_project_data()

    for item in normalized_fields:
        if item["value"] is None:
            continue
        set_nested_value(data, item["path"], item["value"])

    return data


def extract_project_data_from_contexts(
    ai_client,
    project_context,
    methodology_context,
):
    extracted = extract_fields_with_ai(
        ai_client=ai_client,
        project_context=project_context,
        methodology_context=methodology_context,
        fields=EXTRACTION_FIELDS,
    )

    normalized = normalize_extracted_fields(extracted, EXTRACTION_FIELDS)
    project_data = build_project_data_from_extraction(normalized)

    return {
        "project_data": project_data,
        "normalized_fields": normalized,
        "raw_extraction": extracted,
    }
