from typing import Any, Dict, List, Optional

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


DOMAIN_HINTS = {
    "eligibility": ["net negative", "durability", "additionality", "lca"],
    "production": ["maintenance plan", "pfd", "p&id", "reactor", "sensor"],
    "sampling": ["sampling", "batch", "24-hour", "per production batch"],
}


def _safe_text_from_hit(hit: Dict[str, Any]) -> str:
    for key in ["text", "content", "snippet", "chunk_text"]:
        value = hit.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _score_text_for_hints(text: str, hints: List[str]) -> int:
    lowered = text.lower()
    return sum(1 for h in hints if h in lowered)


def _build_domain_context_from_hits(
    hits: List[Dict[str, Any]],
    methodology_context: str,
    domain_name: str,
    max_hits: int = 8,
) -> str:
    hints = DOMAIN_HINTS.get(domain_name, [])

    scored = []
    for i, hit in enumerate(hits):
        text = _safe_text_from_hit(hit)
        if not text:
            continue

        score = _score_text_for_hints(text, hints)
        if score > 0:
            scored.append((i, score, text))

    scored.sort(key=lambda x: (-x[1], x[0]))
    top = [x[2] for x in scored[:max_hits]]

    if len(top) < 3:
        top = [_safe_text_from_hit(h) for h in hits[:max_hits]]

    return "\n\n".join(top)


def _build_domain_contexts(
    project_context: str,
    methodology_context: str,
    project_hits: List[Dict[str, Any]],
) -> Dict[str, str]:
    return {
        "eligibility": _build_domain_context_from_hits(project_hits, methodology_context, "eligibility"),
        "production": _build_domain_context_from_hits(project_hits, methodology_context, "production"),
        "sampling": _build_domain_context_from_hits(project_hits, methodology_context, "sampling"),
        "global": project_context or "",
    }


def run_mapper_pipeline(
    ai_client,
    project_context: str,
    methodology_context: str,
    project_hits: Optional[List[Dict[str, Any]]] = None,
    methodology_hits: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    raw_bundle: Dict[str, Any] = {}
    collected: List[Dict[str, Any]] = []

    project_hits = project_hits or []

    domain_contexts = _build_domain_contexts(
        project_context,
        methodology_context,
        project_hits,
    )

    mapper_runs = [
        ("eligibility_mapper", run_eligibility_mapper, "eligibility"),
        ("production_mapper", run_production_mapper, "production"),
        ("sampling_mapper", run_sampling_mapper, "sampling"),
    ]

    for name, fn, domain in mapper_runs:
        ctx = domain_contexts.get(domain, project_context)

        result = fn(
            ai_client=ai_client,
            project_context=ctx,
            methodology_context=methodology_context,
        )

        raw_bundle[name] = {
            "domain": domain,
            "project_context_used": ctx,
        }

        collected.extend(result.get("normalized_fields", []))

    merged = merge_normalized_fields(collected)

    missing_paths = find_missing_paths(merged, EXTRACTION_FIELDS)

    fallback_result = run_fallback_mapper(
        ai_client=ai_client,
        project_context=project_context,
        methodology_context=methodology_context,
        missing_paths=missing_paths,
    )

    raw_bundle["fallback_mapper"] = {}

    merged = merge_normalized_fields(
        merged + fallback_result.get("normalized_fields", [])
    )

    return {
        "normalized_fields": merged,
        "raw_extraction_bundle": raw_bundle,
    }
