# engine/mappers/__init__.py

from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import find_missing_paths, merge_normalized_fields
from engine.mappers.eligibility_mapper import run_eligibility_mapper
from engine.mappers.additionality_mapper import run_additionality_mapper
from engine.mappers.durability_mapper import run_durability_mapper
from engine.mappers.production_mapper import run_production_mapper
from engine.mappers.sampling_mapper import run_sampling_mapper
from engine.mappers.feedstock_mapper import run_feedstock_mapper
from engine.mappers.storage_mapper import run_storage_mapper
from engine.mappers.quantification_mapper import run_quantification_mapper
from engine.mappers.traceability_mapper import run_traceability_mapper
from engine.mappers.fallback_mapper import run_fallback_mapper


def run_mapper_pipeline(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    raw_bundle: Dict[str, Any] = {}
    collected: List[Dict[str, Any]] = []

    mapper_runs = [
        ("eligibility_mapper", run_eligibility_mapper),
        ("additionality_mapper", run_additionality_mapper),
        ("durability_mapper", run_durability_mapper),
        ("production_mapper", run_production_mapper),
        ("sampling_mapper", run_sampling_mapper),
        ("feedstock_mapper", run_feedstock_mapper),
        ("storage_mapper", run_storage_mapper),
        ("quantification_mapper", run_quantification_mapper),
        ("traceability_mapper", run_traceability_mapper),
    ]

    for name, fn in mapper_runs:
        result = fn(
            ai_client=ai_client,
            project_context=project_context,
            methodology_context=methodology_context,
        )
        raw_bundle[name] = result.get("raw_extraction", {"fields": []})
        collected.extend(result.get("normalized_fields", []))

    merged = merge_normalized_fields(collected)
    missing_paths = find_missing_paths(merged, EXTRACTION_FIELDS)

    fallback_result = run_fallback_mapper(
        ai_client=ai_client,
        project_context=project_context,
        methodology_context=methodology_context,
        missing_paths=missing_paths,
    )
    raw_bundle["fallback_mapper"] = fallback_result.get("raw_extraction", {"fields": []})

    merged = merge_normalized_fields(
        merged + fallback_result.get("normalized_fields", [])
    )

    return {
        "normalized_fields": merged,
        "raw_extraction_bundle": raw_bundle,
    }
