from typing import Any, Dict, List, Optional

from schemas.project_schema import get_empty_project_data

from engine.inference import run_inference_layer
from engine.mappers import run_mapper_pipeline
from engine.mappers.consistency import run_consistency_checks


def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    keys = path.split(".")
    cursor = data

    for key in keys[:-1]:
        if key not in cursor or not isinstance(cursor[key], dict):
            cursor[key] = {}
        cursor = cursor[key]

    cursor[keys[-1]] = value


def build_project_data_from_extraction(
    normalized_fields: List[Dict[str, Any]],
) -> Dict[str, Any]:
    data = get_empty_project_data()

    for item in normalized_fields:
        value = item.get("value")
        path = item.get("path")

        if value is None or not path:
            continue

        set_nested_value(data, path, value)

    return data


def extract_project_data_from_contexts(
    ai_client,
    project_context: str,
    methodology_context: str,
    project_hits: Optional[List[Dict[str, Any]]] = None,
    methodology_hits: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    pipeline_output = run_mapper_pipeline(
        ai_client=ai_client,
        project_context=project_context,
        methodology_context=methodology_context,
        project_hits=project_hits or [],
        methodology_hits=methodology_hits or [],
    )

    normalized_fields = pipeline_output.get("normalized_fields", []) or []
    raw_extraction_bundle = pipeline_output.get("raw_extraction_bundle", {}) or {}

    inference_output = run_inference_layer(
        normalized_fields=normalized_fields,
        raw_extraction_bundle=raw_extraction_bundle,
        project_context=project_context,
        methodology_context=methodology_context,
    )

    normalized_fields = inference_output.get("normalized_fields", []) or normalized_fields
    inference_events = inference_output.get("inference_events", []) or []

    project_data = build_project_data_from_extraction(normalized_fields)

    consistency_output = run_consistency_checks(
        project_data=project_data,
        normalized_fields=normalized_fields,
    )

    return {
        "project_data": project_data,
        "normalized_fields": normalized_fields,
        "raw_extraction": raw_extraction_bundle,
        "inference_events": inference_events,
        "consistency_flags": consistency_output.get("consistency_flags", []),
        "consistency_notes": consistency_output.get("consistency_notes", []),
    }
