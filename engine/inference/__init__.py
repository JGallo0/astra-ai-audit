# engine/inference/__init__.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .registry import INFERENCE_RULES


def run_inference_layer(
    normalized_fields: List[Dict[str, Any]],
    raw_extraction_bundle: Optional[Dict[str, Any]] = None,
    project_context: str = "",
    methodology_context: str = "",
) -> Dict[str, Any]:
    current_fields = list(normalized_fields or [])
    all_inference_events: List[Dict[str, Any]] = []

    for rule in INFERENCE_RULES:
        output = rule.run(
            normalized_fields=current_fields,
            raw_extraction_bundle=raw_extraction_bundle or {},
            project_context=project_context or "",
            methodology_context=methodology_context or "",
        )

        current_fields = output.get("normalized_fields", current_fields)
        all_inference_events.extend(output.get("inference_events", []))

    return {
        "normalized_fields": current_fields,
        "inference_events": all_inference_events,
    }
